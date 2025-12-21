"""Export analysis results to JSON for clean reading."""
import json
from collections import Counter, defaultdict
from pathlib import Path

OUTPUT_DIR = r"d:\tareas\PBT\pbt_outputs"

def load_all_packages():
    packages = []
    for f in Path(OUTPUT_DIR).glob("prompt_package_*.json"):
        try:
            with open(f, 'r', encoding='utf-8') as file:
                data = json.load(file)
                data['_filename'] = f.name
                packages.append(data)
        except:
            pass
    return packages

def analyze(packages):
    results = {}
    
    # Score analysis
    scores = []
    score_breakdown = defaultdict(list)
    for p in packages:
        if 'evaluation' in p and 'total_score' in p['evaluation']:
            total = p['evaluation']['total_score']
            scores.append({'topic': p.get('topic', 'Unknown'), 'score': total})
            if 'scores' in p['evaluation']:
                for criterion, score in p['evaluation']['scores'].items():
                    score_breakdown[criterion].append(score)
    
    vals = [s['score'] for s in scores]
    results['scores'] = {
        'count': len(vals),
        'min': min(vals) if vals else 0,
        'max': max(vals) if vals else 0,
        'avg': sum(vals)/len(vals) if vals else 0,
        'excellent_90plus': sum(1 for s in vals if s >= 90),
        'good_75_89': sum(1 for s in vals if 75 <= s < 90),
        'needs_work_60_74': sum(1 for s in vals if 60 <= s < 75),
        'poor_below_60': sum(1 for s in vals if s < 60),
        'top_5': sorted(scores, key=lambda x: x['score'], reverse=True)[:5],
        'bottom_5': sorted(scores, key=lambda x: x['score'])[:5],
        'by_criterion': {k: {'avg': sum(v)/len(v), 'count': len(v)} for k, v in score_breakdown.items()}
    }
    
    # Title analysis
    title_issues = Counter()
    title_scores = []
    for p in packages:
        if 'title_validation' in p:
            tv = p['title_validation']
            title_scores.append({'topic': p.get('topic', ''), 'score': tv.get('score', 0)})
            for issue in tv.get('issues', []):
                title_issues[issue] += 1
    
    results['titles'] = {
        'good_count': sum(1 for t in title_scores if t['score'] >= 0.7),
        'poor_count': sum(1 for t in title_scores if t['score'] < 0.7),
        'common_issues': dict(title_issues.most_common()),
        'good_examples': [t['topic'] for t in title_scores if t['score'] >= 0.7][:5],
        'poor_examples': [t['topic'] for t in title_scores if t['score'] < 0.7][:5]
    }
    
    # Variable analysis
    all_vars = Counter()
    var_counts = []
    for p in packages:
        vars_list = p.get('variables', [])
        var_counts.append(len(vars_list))
        for v in vars_list:
            all_vars[v.upper()] += 1
    
    results['variables'] = {
        'count_distribution': dict(Counter(var_counts)),
        'most_common': dict(all_vars.most_common(15))
    }
    
    # Platform analysis
    platforms = Counter()
    content_types = Counter()
    categories = Counter()
    for p in packages:
        platforms[p.get('platform', 'Unknown')] += 1
        content_types[p.get('content_type', 'Unknown')] += 1
        categories[p.get('category', 'Unknown')] += 1
    
    results['distribution'] = {
        'platforms': dict(platforms.most_common()),
        'content_types': dict(content_types.most_common()),
        'categories': dict(categories.most_common())
    }
    
    # Improvement patterns
    keywords = Counter()
    keyword_list = ['title', 'example', 'shorten', 'diversify', 'add', 
                    'variable', 'description', 'length', 'word', 'expand',
                    'revise', 'strengthen', 'abstract']
    all_improvements = []
    for p in packages:
        if 'evaluation' in p and 'priority_improvements' in p['evaluation']:
            for imp in p['evaluation']['priority_improvements']:
                all_improvements.append(imp)
                for kw in keyword_list:
                    if kw in imp.lower():
                        keywords[kw] += 1
    
    results['improvements'] = {
        'total_suggestions': len(all_improvements),
        'keyword_frequency': dict(keywords.most_common()),
        'sample_suggestions': all_improvements[:10]
    }
    
    return results

packages = load_all_packages()
results = analyze(packages)
results['package_count'] = len(packages)

with open('analysis_results.json', 'w', encoding='utf-8') as f:
    json.dump(results, f, indent=2, ensure_ascii=False)

print(f"Analysis complete. {len(packages)} packages analyzed.")
print("Results saved to analysis_results.json")
