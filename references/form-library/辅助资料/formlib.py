#!/usr/bin/env python3
"""Local, reference-only form library; Python standard library, no remote writes."""
import argparse
import concurrent.futures
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import re
import sys
import tempfile
import urllib.error
import urllib.request
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parent.parent
VALID_STATUSES = {'verified_visual', 'source_only', 'needs_evidence'}
PROJECT_STATUSES = {'built', 'concept', 'render', 'unknown'}
DATE = '2026-10-09'


def unique_object(pairs):
    out = {}
    for k, v in pairs:
        if k in out:
            raise ValueError(f'重复 JSON 键: {k}')
        out[k] = v
    return out


def read_json(path):
    return json.loads(Path(path).read_text(encoding='utf-8'), object_pairs_hook=unique_object,
                      parse_constant=lambda s: (_ for _ in ()).throw(ValueError(s)))


def atomic_text(path, content):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix='.' + path.name, dir=path.parent)
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as stream:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def write_json(path, obj):
    atomic_text(path, json.dumps(obj, ensure_ascii=False, indent=2) + '\n')


def safe_new_output(path):
    out = Path(path).resolve()
    if out.is_relative_to(ROOT / 'data') or out == (ROOT / 'index.html').resolve() or out.suffix != '.json':
        raise ValueError('输出必须另存为 JSON，不能写入知识库 data 或覆盖浏览入口')
    if out.exists():
        raise ValueError('输出已存在；使用新文件名以保留记录')
    return out


def is_url(value):
    if not isinstance(value, str):
        return False
    parsed = urlsplit(value)
    return parsed.scheme == 'https' and bool(parsed.hostname) and not parsed.username and not parsed.password


def validate(lib, taxonomy):
    errors = []
    cats = {c['id'] for c in taxonomy['categories']}
    styles = {s['name'] for s in taxonomy.get('styles', [])}
    if not isinstance(lib, dict) or not isinstance(lib.get('forms'), list) or not isinstance(lib.get('sources'), list):
        return ['forms 和 sources 必须是列表']
    if lib.get('schema') != 'interior-form-library/1.0' or not isinstance(lib.get('version'), str):
        errors.append('缺少有效的知识库 schema/version')
    ids, sources = set(), {}
    for s in lib['sources']:
        if not isinstance(s, dict):
            errors.append('每个来源必须是对象')
            continue
        sid = s.get('id')
        if not sid or sid in sources:
            errors.append(f'无效或重复来源 ID: {sid}')
        sources[sid] = s
        for key in ('title', 'publisher', 'project', 'verified_at', 'access_status', 'status_basis'):
            if not isinstance(s.get(key), str) or not s[key].strip():
                errors.append(f'{sid}: 缺少 {key}')
        if not is_url(s.get('url')):
            errors.append(f'{sid}: 来源必须为真实 HTTPS 链接')
        if s.get('project_status') not in PROJECT_STATUSES:
            errors.append(f'{sid}: 无效项目状态')
        if s.get('rights') != 'reference_only_no_download':
            errors.append(f'{sid}: 本库仅收录在线引用；原图许可需要另存明确证据')
    for f in lib['forms']:
        if not isinstance(f, dict):
            errors.append('每个造型必须是对象')
            continue
        fid = f.get('id')
        if not isinstance(fid, str) or not re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)+', fid) or fid in ids:
            errors.append(f'无效或重复造型 ID: {fid}')
        ids.add(fid)
        if f.get('category') not in cats:
            errors.append(f'{fid}: 未登记类别')
        for key in ('name_zh', 'name_en', 'distinctions'):
            if not isinstance(f.get(key), str) or not f[key].strip():
                errors.append(f'{fid}: 缺少 {key}')
        for key in ('aliases', 'visual_features', 'spatial_applications', 'style_tags', 'combinations', 'source_ids', 'evidence'):
            if not isinstance(f.get(key), list):
                errors.append(f'{fid}: {key} 必须为列表')
        if any(not isinstance(f.get(key), list) for key in ('aliases', 'visual_features', 'spatial_applications', 'style_tags', 'combinations', 'source_ids', 'evidence')):
            continue
        for key in ('aliases', 'visual_features', 'spatial_applications', 'style_tags', 'combinations', 'source_ids'):
            if any(not isinstance(v, str) or not v.strip() for v in f[key]):
                errors.append(f'{fid}: {key} 只能含非空文字')
        for style in f['style_tags']:
            if style not in styles:
                errors.append(f'{fid}: 风格未登记 {style}')
        if len(f.get('visual_features', [])) < 3:
            errors.append(f'{fid}: 至少三条可辨识视觉特征')
        if not f.get('spatial_applications') or not f.get('style_tags') or not f.get('combinations'):
            errors.append(f'{fid}: 缺少适用空间、风格或组合关系')
        if f.get('status') not in VALID_STATUSES:
            errors.append(f'{fid}: 无效状态')
        for sid in f.get('source_ids', []):
            if sid not in sources:
                errors.append(f'{fid}: 未找到来源 {sid}')
        observed = False
        for e in f.get('evidence', []):
            if not isinstance(e, dict):
                errors.append(f'{fid}: 图片观察必须是对象')
                continue
            sid = e.get('source_id')
            if sid not in sources or sid not in f.get('source_ids', []):
                errors.append(f'{fid}: 图片观察关联了未登记来源 {sid}')
            if e.get('image_url') is not None and not is_url(e['image_url']):
                errors.append(f'{fid}: 图片地址无效')
            if not is_url(e.get('gallery_url')):
                errors.append(f'{fid}: 缺少有效图库/项目入口')
            if e.get('visual_status') == 'observed':
                observed = True
                for key in ('observation', 'view_method', 'checked_at'):
                    if not e.get(key):
                        errors.append(f'{fid}: 实际观察缺少 {key}')
            elif e.get('visual_status') != 'unverified':
                errors.append(f'{fid}: 无效视觉核验状态')
        if f.get('status') == 'verified_visual' and not observed:
            errors.append(f'{fid}: 没有视觉观察却标为已看图')
        if f.get('status') == 'verified_visual' and not f.get('source_ids'):
            errors.append(f'{fid}: 没有原始来源')
    return errors


def stats(lib, taxonomy):
    forms, sources = lib['forms'], lib['sources']
    return {
        'form_count': len(forms),
        'by_category': {c['name_zh']: sum(f['category'] == c['id'] for f in forms) for c in taxonomy['categories']},
        'source_count': len(sources),
        'verified_source_count': sum(s['access_status'] in {'verified', 'accessible', 'verified_page', 'readable', 'verified_browser'} for s in sources),
        'visually_observed_forms': sum(any(e['visual_status'] == 'observed' for e in f['evidence']) for f in forms),
        'missing_visual_forms': [f['id'] for f in forms if not any(e['visual_status'] == 'observed' for e in f['evidence'])],
        'missing_direct_image_forms': [f['id'] for f in forms if not any(e.get('image_url') for e in f['evidence'])],
        'source_project_statuses': {s: sum(x['project_status'] == s for x in sources) for s in sorted(PROJECT_STATUSES)},
        'source_only_forms': [f['id'] for f in forms if f['status'] == 'source_only'],
        'needs_evidence_forms': [f['id'] for f in forms if f['status'] == 'needs_evidence'],
        'data_sha256': hashlib.sha256(json.dumps(lib, ensure_ascii=False, sort_keys=True).encode()).hexdigest(),
    }


def normalized(s):
    return re.sub(r'[\s_-]+', '', s.casefold())


def category_id(value, taxonomy):
    if not value:
        return None
    needle = normalized(value)
    for c in taxonomy['categories']:
        if needle in {normalized(x) for x in [c['id'], c['name_zh'], c['name_en'], *c.get('aliases', [])]}:
            return c['id']
    raise ValueError(f'未知构件类别: {value}')


def style_label(value, taxonomy):
    needle = normalized(value)
    for s in taxonomy.get('styles', []):
        if needle in {normalized(x) for x in [s['name'], *s.get('aliases', [])]}:
            return s['name']
    return value


def enriched(f, lib):
    out = dict(f)
    sources = {s['id']: s for s in lib['sources']}
    out['references'] = [sources[sid] for sid in f['source_ids']]
    out['interpretation_basis'] = '视觉特征来自本轮多模态看图与编辑归纳；适用空间、风格及组合关系为设计参考建议，非原作者声明。'
    return out


def search(lib, taxonomy, query='', category=None, styles=None, room='', include_unverified=False, limit=12):
    cat = category_id(category, taxonomy)
    room = taxonomy.get('spatial_aliases', {}).get(room, room)
    style_set = {style_label(s, taxonomy) for s in styles or []}
    q = normalized(query)
    tokens = [normalized(t) for t in re.split(r'\s+', query) if t]
    results = []
    for f in lib['forms']:
        if cat and f['category'] != cat:
            continue
        if not include_unverified and f['status'] != 'verified_visual':
            continue
        if style_set and not style_set.issubset(set(f['style_tags'])):
            continue
        if room and not any(normalized(room) in normalized(s) for s in f['spatial_applications']):
            continue
        names = [f['id'], f['name_zh'], f['name_en'], *f['aliases']]
        normalized_names = [normalized(n) for n in names]
        # Comparison text may name forms that this item explicitly differs from.
        description = normalized(' '.join(f['visual_features']))
        score = 1
        if q:
            if any(q == normalized(x) for x in names):
                score = 100
            elif any(q in n for n in normalized_names):
                score = 70
            elif tokens and all(any(t in n for n in normalized_names) or t in description for t in tokens):
                score = 30 + sum(any(t in n for n in normalized_names) for t in tokens) * 10
            else:
                continue
        results.append((score, f))
    results.sort(key=lambda x: (-x[0], x[1]['category'], x[1]['id']))
    return {'schema': 'interior-form-search/1.0', 'library_version': lib.get('version'),
            'total_matches': len(results), 'returned': min(len(results), limit),
            'filters': {'query': query, 'category': cat, 'styles': sorted(style_set), 'room': room, 'include_unverified': include_unverified},
            'results': [dict(enriched(f, lib), match_score=score) for score, f in results[:limit]]}


def selection(lib, ids, room='', style=''):
    lookup = {f['id']: f for f in lib['forms']}
    if len(ids) != len(set(ids)):
        raise ValueError('重复的造型 ID')
    missing = [x for x in ids if x not in lookup]
    if missing:
        raise ValueError('未知造型 ID: ' + ', '.join(missing))
    selected = [enriched(lookup[x], lib) for x in ids]
    warnings = []
    for f in selected:
        if f['status'] != 'verified_visual':
            warnings.append(f"{f['name_zh']} 缺少已观察视觉证据，不应作为已核实造型自动采用。")
        if style and style not in f['style_tags']:
            warnings.append(f"{f['name_zh']} 未登记 {style} 适配；需按本案判断。")
        if room and not any(room in s for s in f['spatial_applications']):
            warnings.append(f"{f['name_zh']} 未登记 {room} 适用性；需按本案判断。")
        if any(s['project_status'] != 'built' for s in f['references']):
            warnings.append(f"{f['name_zh']} 的出处含非建成或建成状态未确认记录；仅作为视觉参考，不称为已核实建成案例。")
    return {'schema': 'interior-form-selection/1.0', 'library_version': lib.get('version'),
            'room': room, 'design_style': style, 'selection_state': 'candidate', 'selected_forms': selected,
            'design_brief': '\n'.join(f"{f['name_zh']}（{f['name_en']}）：" + '；'.join(f['visual_features']) + '。组合：' + '；'.join(f['combinations']) for f in selected),
            'warnings': warnings,
            'handoff': '保留本案已确认的墙门窗、布局与占位。参考案例只提供构件造型；选型被确认后由现有流程承接建模与渲染。此包不含尺寸、施工节点、3D 模型或生图授权。'}


def check_link(url):
    request = urllib.request.Request(url, method='HEAD', headers={'User-Agent': 'Mozilla/5.0 (InteriorFormLibrary link check)'})
    try:
        with urllib.request.urlopen(request, timeout=18) as res:
            return {'url': url, 'status': res.status, 'final_url': res.geturl(), 'content_type': res.headers.get('Content-Type'), 'result': 'reachable'}
    except urllib.error.HTTPError as e:
        return {'url': url, 'status': e.code, 'result': 'head_rejected_or_unavailable', 'note': 'HEAD失败不等于项目或图片不存在；回到浏览器核对。'}
    except Exception as e:
        return {'url': url, 'status': None, 'result': 'not_reachable_from_this_check', 'error': str(e)[:240]}


def build_viewer(lib, taxonomy):
    payload = dict(library=lib, taxonomy=taxonomy, stats=stats(lib, taxonomy))
    # Never permit a source string to terminate the non-executable JSON script block.
    json_text = json.dumps(payload, ensure_ascii=False).replace('<', '\\u003c').replace('>', '\\u003e').replace('&', '\\u0026')
    template = (ROOT / '辅助资料' / 'viewer.template.html').read_text(encoding='utf-8')
    return template.replace('__LIBRARY_PAYLOAD__', json_text)


def emit(obj):
    print(json.dumps(obj, ensure_ascii=False, indent=2))


def main():
    global ROOT
    parser = argparse.ArgumentParser(description='室内设计造型库：本地检索、选型包、校验与安全导入')
    parser.add_argument('--root', type=Path, default=ROOT, help='知识库根目录；移动文件夹后可继续调用')
    subs = parser.add_subparsers(dest='command', required=True)
    p = subs.add_parser('search')
    p.add_argument('query', nargs='?', default='')
    p.add_argument('--category')
    p.add_argument('--style', action='append', default=[])
    p.add_argument('--room', default='')
    p.add_argument('--include-unverified', action='store_true')
    p.add_argument('--limit', type=int, default=12)
    p = subs.add_parser('show'); p.add_argument('id')
    p = subs.add_parser('select'); p.add_argument('ids', nargs='+'); p.add_argument('--room', default=''); p.add_argument('--style', default=''); p.add_argument('--out', type=Path)
    subs.add_parser('validate'); subs.add_parser('stats'); subs.add_parser('build')
    p = subs.add_parser('import'); p.add_argument('proposal', type=Path); p.add_argument('--apply', action='store_true'); p.add_argument('--replace-existing', action='store_true')
    p = subs.add_parser('check-links'); p.add_argument('--images', action='store_true'); p.add_argument('--out', type=Path); p.add_argument('--workers', type=int, default=5)
    args = parser.parse_args()
    ROOT = args.root.resolve()
    libpath = ROOT / 'data' / 'library.json'
    lib, taxonomy = read_json(libpath), read_json(ROOT / 'data' / 'taxonomy.json')
    errors = validate(lib, taxonomy)
    if args.command == 'validate':
        emit({'valid': not errors, 'errors': errors, 'stats': stats(lib, taxonomy) if not errors else None}); return 0 if not errors else 2
    if errors:
        raise ValueError('数据校验失败: ' + '; '.join(errors))
    if args.command == 'stats':
        emit(stats(lib, taxonomy))
    elif args.command == 'search':
        if not 1 <= args.limit <= 500:
            raise ValueError('limit 须在 1–500 之间')
        emit(search(lib, taxonomy, args.query, args.category, args.style, args.room, args.include_unverified, args.limit))
    elif args.command == 'show':
        found = next((f for f in lib['forms'] if f['id'] == args.id), None)
        if found is None:
            raise ValueError('未知造型 ID: ' + args.id)
        emit(enriched(found, lib))
    elif args.command == 'select':
        result = selection(lib, args.ids, taxonomy.get('spatial_aliases', {}).get(args.room, args.room), style_label(args.style, taxonomy) if args.style else '')
        if args.out:
            out = safe_new_output(args.out)
            write_json(out, result)
        emit(result)
    elif args.command == 'build':
        atomic_text(ROOT / 'index.html', build_viewer(lib, taxonomy)); emit({'built': str(ROOT / 'index.html'), 'stats': stats(lib, taxonomy)})
    elif args.command == 'import':
        proposal = read_json(args.proposal)
        merged = json.loads(json.dumps(lib))
        changes = {'forms': [], 'sources': []}
        for field in ('forms', 'sources'):
            candidates = proposal.get(field, [])
            if not isinstance(candidates, list) or any(not isinstance(x, dict) or not isinstance(x.get('id'), str) for x in candidates):
                raise ValueError(f'{field} 必须是含字符串 ID 的对象列表')
            if len({x['id'] for x in candidates}) != len(candidates):
                raise ValueError(f'候选 {field} 包含重复 ID')
            old = {x['id']: x for x in merged[field]}
            for item in candidates:
                if item['id'] in old and old[item['id']] != item and not args.replace_existing:
                    raise ValueError(f"{item['id']} 已存在；修正需显式 --replace-existing")
                if old.get(item['id']) != item:
                    changes[field].append(item['id'])
                old[item['id']] = item
            merged[field] = list(old.values())
        merged['updated_at'] = dt.datetime.now(dt.timezone.utc).isoformat()
        errors = validate(merged, taxonomy)
        if errors:
            raise ValueError('候选导入失败: ' + '; '.join(errors))
        if args.apply and any(changes.values()):
            # Local lock prevents another supported importer from racing this transaction.
            import fcntl
            with open(ROOT / '辅助资料' / '.import.lock', 'a') as lock:
                fcntl.flock(lock, fcntl.LOCK_EX)
                if read_json(libpath) != lib:
                    raise ValueError('数据已被其他进程更改；重新预览导入')
                stamp = dt.datetime.now(dt.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
                backup = ROOT / '辅助资料' / '维护记录' / f'library-before-{stamp}.json'
                viewer = build_viewer(merged, taxonomy)
                viewerpath = ROOT / 'index.html'
                if viewerpath.exists() and not viewerpath.is_file():
                    raise ValueError('浏览入口路径不是普通文件；数据尚未应用')
                old_viewer = viewerpath.read_text(encoding='utf-8') if viewerpath.exists() else None
                write_json(backup, lib)
                recordpath = ROOT / '辅助资料' / '维护记录' / f'import-{stamp}.json'
                record = {'proposal': str(args.proposal), 'changes': changes, 'backup': str(backup), 'status': 'prepared'}
                write_json(recordpath, record)
                try:
                    write_json(libpath, merged)
                    atomic_text(viewerpath, viewer)
                    write_json(recordpath, dict(record, status='applied'))
                except OSError as apply_error:
                    # Restore both authoritative data and its view if any commit step fails.
                    try:
                        write_json(libpath, lib)
                        if old_viewer is not None:
                            atomic_text(viewerpath, old_viewer)
                        elif viewerpath.exists():
                            viewerpath.unlink()
                        write_json(recordpath, dict(record, status='rolled_back', error=str(apply_error)))
                    except OSError as rollback_error:
                        raise ValueError(f'应用中断且回滚未能完成。备份保留在 {backup}；请从备份核对并重建。应用错误: {apply_error}；回滚错误: {rollback_error}') from rollback_error
                    raise ValueError(f'导入未应用，已回滚数据与网页。原因: {apply_error}') from apply_error
        emit({'applied': args.apply and any(changes.values()), 'changes': changes, 'valid': True, 'stats': stats(merged, taxonomy)})
    elif args.command == 'check-links':
        if not 1 <= args.workers <= 10:
            raise ValueError('workers 须在 1–10 之间')
        out = safe_new_output(args.out) if args.out else None
        urls = {s['url'] for s in lib['sources']}
        if args.images:
            urls |= {e['image_url'] for f in lib['forms'] for e in f['evidence'] if e.get('image_url')}
        with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as pool:
            records = list(pool.map(check_link, sorted(urls)))
        result = {'checked_at': dt.datetime.now(dt.timezone.utc).isoformat(), 'method': 'HTTP HEAD only; no image body downloaded', 'count': len(records), 'records': records}
        if out:
            write_json(out, result)
        emit({'checked': len(records), 'reachable': sum(r['result'] == 'reachable' for r in records), 'requires_browser_check': sum(r['result'] != 'reachable' for r in records), 'report': str(args.out) if args.out else None})
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except (ValueError, OSError, KeyError, TypeError) as error:
        emit({'error': str(error)}); sys.exit(2)
