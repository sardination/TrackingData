# -*- coding: utf-8 -*-
"""
Created on Tue Jan 29 16:06:54 2019

Module for reading Tracab data and constructing frame and player objects

@author: laurieshaw
"""

from bs4 import BeautifulSoup
import datetime as dt
import numpy as np
import Tracking_Velocities as vel

def read_tracab_match(fmetadata):
    # get meta data
    f = open(fmetadata, "r")
    metadata = f.read()
    soup = BeautifulSoup(metadata, 'xml') # deal with xml markup (BS might be overkill here)
    match_attributes = soup.match.attrs
    period_attributes = {}
    # navigate through the file to extract the info that we need
    for p in soup.find_all('period'):
        if p.attrs['iEndFrame']>p.attrs['iStartFrame']:
            period_attributes[int(p.attrs['iId'])] = p.attrs
    match = tracab_match(match_attributes, period_attributes)
    return match

def read_tracab_match_data(fpath,fname,during_match_only=True, verbose=False):
    # get match metadata
    if verbose:
        print "Reading match metadata"
    fmetadata = fpath+'TracabMetadata'+fname
    match = read_tracab_match(fmetadata)
    # now read in tracking data
    if verbose:
        print "Reading match tracking data"
    fdata = fpath+'TracabData'+fname
    frames = []
    with open(fdata, "r") as fp:
        for f in fp: # go through line by line and break down data in individual players and the ball
            # each line is a single frame
            chunks = f.split(':')[:-1] # last element is carriage return
            if len(chunks)>3:
                print chunks
            assert len(chunks)<=3
            frameid = int(chunks[0])
            frame = tracab_frame(frameid)
            # now get players
            targets = chunks[1].split(';')
            assert targets[-1]==''
            for target in targets[:-1]:
                target = target.split(',')
                team = int( target[0] )
                if team in [1,0,3]:
                    frame.add_frame_target(target)                    
            if len(chunks)>2: # is this never the case?
                frame.add_frame_ball( chunks[2].split(';')[0].split(',') )
            frames.append(frame)
    # sort the frames by frameid (they should be sorted anyway, but just to make sure)
    frames = sorted(frames,key = lambda x: x.frameid )
    # timestamp frames
    if verbose:
        print "Timestamping frames"
    frames, match = timestamp_frames(frames,match)
    # run some basic checks
    check_frames(frames)
    if during_match_only: # remove pre-match, post-match and half-time frames
        frames = frames[match.period_attributes[1]['iStart']:match.period_attributes[1]['iEnd']+1] + frames[match.period_attributes[2]['iStart']:match.period_attributes[2]['iEnd']+1]
        match.period_attributes[1]['iEnd'] = match.period_attributes[1]['iEnd']-match.period_attributes[1]['iStart']
        match.period_attributes[1]['iStart'] = 0
        match.period_attributes[2]['iEnd'] = match.period_attributes[2]['iEnd'] - match.period_attributes[2]['iStart'] + match.period_attributes[1]['iEnd']
        match.period_attributes[2]['iStart'] = match.period_attributes[1]['iEnd']+1
    # get player objects and calculate ball and player velocity 
    if verbose:
        print "Measuring velocities"
    team1_players, team0_players = get_players(frames)
    vel.estimate_player_velocities(team1_players, team0_players, match, window=7, polyorder=1, maxspeed = 14)
    vel.estimate_ball_velocities(frames,match,window=5,polyorder=3,maxspeed=40)
    return frames, match, team1_players, team0_players

def check_frames(frames):
    frameids = [frame.frameid for frame in frames]
    missing = set(frameids).difference(set(range(min(frameids),max(frameids)+1)))
    nduplicates = len(frameids)-len(np.unique(frameids))
    if len(missing)>0:
        print "Check Fail: Missing frames"
    if nduplicates>0:
        print "Check Fail: Duplicate frames found"

def get_players(frames):
    # first get all players that appear in at least one frame
    # get all jerseys in frames
    team1_jerseys = set([]) # home team 
    team0_jerseys = set([]) # away team
    team1_players = {}
    team0_players = {}
    for frame in frames:
        team1_jerseys.update( frame.team1_jersey_nums_in_frame )
        team0_jerseys.update( frame.team0_jersey_nums_in_frame )
    for j1 in team1_jerseys:
        team1_players[j1] = tracab_player(j1,1)
    for j0 in team0_jerseys:
        team0_players[j0] = tracab_player(j0,0)
    for frame in frames:
        for j in team1_jerseys:
            if j in frame.team1_jersey_nums_in_frame:
                team1_players[j].add_frame(frame.team1_players[j],frame.frameid,frame.timestamp)
            else: # player is not in this frame
                team1_players[j].add_null_frame(frame.frameid,frame.timestamp)
        for j in team0_jerseys:
            if j in frame.team0_jersey_nums_in_frame:
                team0_players[j].add_frame(frame.team0_players[j],frame.frameid,frame.timestamp)
            else: # player is not in this frame
                team0_players[j].add_null_frame(frame.frameid,frame.timestamp)
    return team1_players, team0_players

def timestamp_frames(frames,match):
    # Frames must be sorted into ascending frameid first
    frame_period = 1/float(match.iFrameRateFps)
    # ASSUMES NO INJURY TIME
    match.period_attributes[1]['iStart'] = None
    match.period_attributes[2]['iStart'] = None
    match.period_attributes[1]['iEnd'] = None
    match.period_attributes[2]['iEnd'] = None
    for i,frame in enumerate(frames):
        if frame.frameid<match.period_attributes[1]['iStartFrame']:
            frame.period = 0 # pre match
            frame.timestamp = -1
        elif frame.frameid>match.period_attributes[2]['iEndFrame']:
            frame.period = 4 # post match
            frame.timestamp = -1
        elif frame.frameid<=match.period_attributes[1]['iEndFrame']:
            frame.period = 1 # first half
            frame.timestamp = (frame.frameid-match.period_attributes[1]['iStartFrame'])*frame_period/60.
            frame.min = str( int(frame.timestamp) )
            frame.sec = "%1.2f" % ( round((frame.timestamp-int(frame.timestamp))*60.,3) )
            if match.period_attributes[1]['iStart'] is None:
                match.period_attributes[1]['iStart'] = i
            if frame.frameid==match.period_attributes[1]['iEndFrame']:
                match.period_attributes[1]['iEnd'] = i
        elif frame.frameid>=match.period_attributes[2]['iStartFrame']:
            frame.period = 2 # second half
            frame.timestamp = (frame.frameid-match.period_attributes[2]['iStartFrame'])*frame_period/60.
            frame.min = str( int(frame.timestamp) )
            frame.sec = "%1.2f" % ( round((frame.timestamp-int(frame.timestamp))*60.,3) )
            if match.period_attributes[2]['iStart'] is None:
                match.period_attributes[2]['iStart'] = i
            if frame.frameid==match.period_attributes[2]['iEndFrame']:
                match.period_attributes[2]['iEnd'] = i
        else:
            frame.period = 3 # half time
            frame.timestamp = -1
    return frames, match


# match class
class tracab_match(object):
    def __init__(self,match_attributes,period_attributes):
        self.provider = 'Tracab'
        self.match_attributes = match_attributes
        self.date = dt.datetime.strptime(match_attributes['dtDate'], '%Y-%m-%d %H:%M:%S')
        self.fPitchXSizeMeters = float(match_attributes['fPitchXSizeMeters'])
        self.fPitchYSizeMeters = float(match_attributes['fPitchYSizeMeters'])
        self.fTrackingAreaXSizeMeters = float(match_attributes['fTrackingAreaXSizeMeters'])
        self.fTrackingAreaYSizeMeters = float(match_attributes['fTrackingAreaYSizeMeters'])
        self.iFrameRateFps = int(match_attributes['iFrameRateFps'])
        for pk in period_attributes.keys():
            for ak in period_attributes[pk].keys():
                period_attributes[pk][ak] = int(period_attributes[pk][ak])
        self.period_attributes = period_attributes
        
# frame class
class tracab_frame(object):
    def __init__(self,frameid):
        self.provider = 'Tracab'
        self.frameid = frameid
        self.team1_players = {}
        self.team0_players = {}
        self.team1_jersey_nums_in_frame = []
        self.team0_jersey_nums_in_frame = []
        self.ball = False
        self.referee = None
        
    def add_frame_target(self,target_raw):
        # add a player to the frame
        team = int( target_raw[0] )
        sys_target_ID = int( target_raw[1] )
        jersey_num = int( target_raw[2] )
        pos_x = float( target_raw[3] ) # useful to make positions a float
        pos_y = float( target_raw[4] )
        speed = float( target_raw[5] )
        if team==1:
            self.team1_players[jersey_num] = tracab_target(team,sys_target_ID,jersey_num,pos_x,pos_y,speed) 
            self.team1_jersey_nums_in_frame.append( jersey_num )
        elif team==0:
            self.team0_players[jersey_num] = tracab_target(team,sys_target_ID,jersey_num,pos_x,pos_y,speed) 
            self.team0_jersey_nums_in_frame.append( jersey_num )
        else:
            self.referee = tracab_target(team,sys_target_ID,jersey_num,pos_x,pos_y,speed) 
    
    def add_frame_ball(self,ball_raw):
        self.ball = True
        self.ball_pos_x = float( ball_raw[0] )
        self.ball_pos_y = float( ball_raw[1] )
        self.ball_pos_z = float( ball_raw[2] )
        self.ball_speed = float( ball_raw[3] ) / 100. # ball speed is in cm/s?
        self.ball_team = ball_raw[4]
        self.ball_status = ball_raw[5]
        if len(ball_raw)==7:
            self.ball_contact_info =ball_raw[6]
        else:
            self.ball_contact_info = None
        
    def __repr__(self):
        nplayers = len(self.team1_jersey_nums_in_frame)+len(self.team1_jersey_nums_in_frame)
        nrefs = 0 if self.referee is None else 1
        s = 'Frame id: %d, nplayers: %d, nrefs: %d, nballs: %d' % (self.frameid, nplayers, nrefs, self.ball*1)
        return s
        
class tracab_target(object):
    # defines position of an individual target 'player' in a frame
    def __init__(self,team,sys_target_ID,jersey_num,pos_x,pos_y,speed):
        self.team = team
        self.sys_target_ID = sys_target_ID
        self.jersey_num = jersey_num
        self.pos_x = pos_x
        self.pos_y = pos_y
        self.speed = speed
        
class tracab_player(object):
    # contains trajectory of a single player over the entire match
    def __init__(self,jersey_num, teamID):
        self.jersey_num = jersey_num
        self.teamID = teamID
        self.frame_targets = []
        self.frame_timestamps = []
        self.frameids = []
        
    def add_frame(self,target,frameid,timestamp):
        self.frame_targets.append( target )
        self.frame_timestamps.append( timestamp )
        self.frameids.append( frameid )
        
    def add_null_frame(self,frameid,timestamp):
        # player is not on the pitch (specifically, is not in a frame)
        self.frame_timestamps.append( timestamp )
        self.frameids.append( frameid )
        self.frame_targets.append( tracab_target(self.teamID, None, self.jersey_num, 0.0, 0.0, 0.0 ) )
        
        
    
    
    
    
    
