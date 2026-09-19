"""実測JSONを集計する。自動操作や未提出の人間評価を合格へ変換しない。"""
from __future__ import annotations
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parent.parent


def summarize(record: dict) -> dict:
    expected=hashlib.sha256((ROOT/'data/campaign_content_v1.json').read_bytes()).hexdigest()
    kinds=Counter(e.get('kind','') for e in record.get('events',[]))
    battles=[e['details'] for e in record.get('events',[]) if e.get('kind')=='battle_finished']
    answers=record.get('answers',[])
    active=record.get('active_ms',0)/60000
    playing=(record.get('active_ms',0)+record.get('idle_ms',0))/60000
    human=record.get('source')=='human' and not record.get('source_changed',False)
    current=record.get('game',{}).get('content_sha256')==expected and record.get('game',{}).get('content_revision')==1
    full=bool(record.get('completed')) and set(record.get('game',{}).get('circuits_completed',[]))=={'waterway','cave','school','records','gate'}
    return {
        'status':'REQUIRES_HUMAN_REVIEW' if human and full and current and answers else 'NOT_ACCEPTED',
        'source':record.get('source','unknown'),'current_content':current,'full_route_recorded':full,
        'elapsed_minutes':round(record.get('elapsed_ms',0)/60000,3),'active_minutes':round(active,3),
        'idle_minutes':round(record.get('idle_ms',0)/60000,3),'pause_minutes':round(record.get('pause_ms',0)/60000,3),
        'foreground_play_minutes':round(playing,3),'idle_review_required':record.get('idle_ms',0)>0,
        'duration_candidate':human and full and current and 300<=playing<=360,
        'human_review_answer_count':len(answers) if human else 0,
        'battles':len(battles),'defeats':sum(not b.get('victory',False) for b in battles),
        'battle_rounds':sum(b.get('rounds',0) for b in battles),'events':dict(kinds),
        'answers':answers if human else [],
        'unverified':['人間が実際に操作したことの確認','探索・報酬・難易度への回答内容の評価'],
    }


def main():
    parser=argparse.ArgumentParser();parser.add_argument('report',type=Path);parser.add_argument('--output',type=Path);args=parser.parse_args()
    record=json.loads(args.report.read_text(encoding='utf-8-sig'))
    result=summarize(record)
    encoded=json.dumps(result,ensure_ascii=False,indent=2)+'\n'
    if args.output:
        args.output.parent.mkdir(parents=True,exist_ok=True)
        args.output.write_text(encoded,encoding='utf-8',newline='\n')
    print(encoded,end='')


if __name__=='__main__':main()
