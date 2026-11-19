"""Named collection blocks. The controller remains the only event scheduler."""
BLOCKS = {
    'stand_still': ('Standing still', 'still', 'standing'),
    'sit_still': ('Seated still', 'still', 'seated'),
    'activities_standing': ('Activities · start standing', 'isolated', 'standing'),
    'activities_standing_makeup': ('P04 standing activities · makeup only', 'isolated', 'standing'),
    'activities_seated': ('Seated activities', 'isolated', 'seated'),
    'signs_standing': ('Standing signs', 'isolated', 'standing'),
    'signs_seated': ('Seated signs', 'isolated', 'seated'),
    'mixed_activity': ('Mixed activity and signs', 'mixed', 'changing'),
    'mixed_meal': ('Mixed meal sequence', 'meal', 'changing'),
    'mixed_tv': ('Mixed TV / phone sequence', 'tv', 'changing'),
    'mixed_cleaning': ('Mixed cleaning sequence', 'cleaning', 'changing'),
}
SEATED_ACTIONS = ['drink', 'answerphone', 'eat', 'wipetable', 'tvremote', 'chop_food', 'stir_pot']

def configure_block(request, actions, signs):
    req = dict(request)
    block = req.get('block')
    if not block:
        return req
    if block not in BLOCKS:
        raise ValueError('Unknown named collection block.')
    title, mode, posture = BLOCKS[block]
    req.update(mode=mode, posture=posture, block_title=title)
    if block == 'activities_standing':
        req['classes'] = [a for a in actions if a != 'fall']
    elif block == 'activities_seated':
        req['classes'] = list(SEATED_ACTIONS)
    elif block.startswith('signs_'):
        req['classes'] = list(signs)
    return req

def named_phases(req):
    """Replay the participant's actual earlier order, without added anchor tasks."""
    import json
    from pathlib import Path
    block=req['block']; phases=[]
    _,mode,posture=BLOCKS[block]
    def add(kind,label,seconds,state='',trial=0,**extra):
        phases.append(dict(kind=kind,label=label,duration_s=seconds,state=state,trial=trial,
            posture=extra.get('posture',posture),script_id=extra.get('script_id',''),run=extra.get('run',''),
            context=extra.get('context',''),intent=extra.get('intent',''),home_action=extra.get('home_action',''),source_trial=extra.get('source_trial',0)))
    if block in ('stand_still','sit_still'):
        label='stand_still' if block=='stand_still' else 'sit_still'
        add('ready',label,3);add('baseline',label,120,'idle',1)
        return phases,dict(order_source='user requested separate 120-second stillness runs',template_pid='',source_labels='')
    makeup=block=='activities_standing_makeup'
    if makeup:
        if req['pid']!='P04':raise ValueError('This makeup block belongs to P04 only.')
        profile=json.loads((Path(__file__).resolve().parent/'p04_standing_makeup.json').read_text())
        profiles={'P04':{block:profile}}
    else:
        profiles=json.loads((Path(__file__).resolve().parent/'previous_collection_protocol.json').read_text())
    template_pid=req['pid'] if req['pid'] in profiles else 'P04'
    key='mixed_activity' if block.startswith('mixed_') else block
    profile=profiles[template_pid][key]
    events=profile['events']
    if block in ('mixed_meal','mixed_tv','mixed_cleaning'):
        prefix={'mixed_meal':'M-','mixed_tv':'T-','mixed_cleaning':'C-'}[block]
        events=[e for e in events if e['script_id'].startswith(prefix)]
    previous_story=None
    for i,event in enumerate(events,1):
        fields={k:event[k] for k in ['posture','script_id','run','context','intent','home_action']}
        fields['source_trial']=event['trial'] if makeup else 0
        story=(event['script_id'],event['run'])
        # Match prior isolated ready/rest timing. Give a clear changeover between stories.
        ready=10 if key=='mixed_activity' and story!=previous_story else 2.5
        add('ready',event['label'],ready,trial=i,**fields)
        add('perform',event['label'],event['duration_s'],event['type'],i,**fields)
        add('rest','stay_still',2,trial=i,**fields)
        previous_story=story
    return phases,dict(order_source='makeup of quality-rejected original trials' if makeup else 'replay of previous participant collection; no new shuffle',
        template_pid=template_pid,source_labels=profile['source'],source_labels_sha256=profile['source_sha256'])
