# -*- coding: utf-8 -*-
"""
This is an example for creating simple plots from various Neo structures.
It includes a function that generates toy data.
"""
from __future__ import division

import numpy as np
import quantities as pq
import neo
from matplotlib import pyplot as plt


def generate_block(n_segments=3, n_channels=8, n_units=3,
                   data_samples=1000, feature_samples=100):
    """
    Generate a block with a single recording channel group and a number of
    segments, recording channels and units with associated analog signals
    and spike trains.
    """
    feature_len = feature_samples / data_samples
    
    # Create container and grouping objects
    segments = [neo.Segment(index=i) for i in xrange(n_segments)]
        
    rcg = neo.RecordingChannelGroup(name='T0')
    rcs = []
    for i in xrange(n_channels):
        rc = neo.RecordingChannel(name='C%d' % i, index=i)
        rc.recordingchannelgroups = [rcg]
        rcs.append(rc)
    rcg.recordingchannels = rcs
    
    units = [neo.Unit('U%d' % i) for i in xrange(n_units)]
    rcg.units = units
    
    block = neo.Block()
    block.segments = segments
    block.recordingchannelgroups = [rcg]
    
    # Create synthetic data
    for i, seg in enumerate(segments):
        feature_pos = np.random.randint(0, data_samples - feature_samples)
        
        # Analog signals: Noise with a single sinewave feature
        for rc in rcs:
            sig = np.random.randn(data_samples)
            sig[feature_pos:feature_pos + feature_samples] += \
                3 * np.sin(np.linspace(0, 2 * np.pi, feature_samples))
            signal = neo.AnalogSignal(sig * pq.mV, sampling_rate=1 * pq.kHz)
            seg.analogsignals.append(signal)
            rc.analogsignals.append(signal)
        
        # Spike trains: Random spike times with elevated rate in short period
        feature_time = feature_pos / data_samples
        for u in units:
            spikes = np.hstack(
                [np.random.rand(20), 
                 np.random.rand(5) * feature_len + feature_time])
            
            train = neo.SpikeTrain(spikes * pq.s, 1 * pq.s)
            seg.spiketrains.append(train)
            u.spiketrains.append(train)
    
    neo.io.tools.create_many_to_one_relationship(block)
    return block
    
block = generate_block()


# In this example, we treat each segment in turn, averaging over the channels
# in each:
for seg in block.segments:
    print("Analysing segment %d" % seg.index)
    
    siglist = seg.analogsignals
    time_points = siglist[0].times
    avg = np.mean(siglist, axis=0)
    
    plt.figure()
    plt.plot(time_points, avg)
    plt.title("Peak response in segment %d: %f" % (seg.index, avg.max()))

# The second alternative is spatial traversal of the data (by channel), with 
# averaging over trials. For example, perhaps you wish to see which physical 
# location produces the strongest response, and each stimulus was the same:

# We assume that our block has only 1 RecordingChannelGroup
rcg = block.recordingchannelgroups[0]
for rc in rcg.recordingchannels:
    print("Analysing channel %d: %s" % (rc.index, rc.name))
    
    siglist = rc.analogsignals
    time_points = siglist[0].times
    avg = np.mean(siglist, axis=0)
    
    plt.figure()
    plt.plot(time_points, avg)
    plt.title("Average response on channel %d" % rc.index)

# There are three ways to access the spike train data: by segment, 
# by recording channel or by unit.

# By Segment. In this example, each Segment represents data from one trial, 
# and we want a peristimulus time histogram (PSTH) for each trial from all 
# units combined:
for seg in block.segments:
    print("Analysing segment %d" % seg.index)
    stlist = [st - st.t_start for st in seg.spiketrains]
    count, bins = np.histogram(np.hstack(stlist))
    plt.figure()
    plt.bar(bins[:-1], count, width=bins[1] - bins[0])
    plt.title("PSTH in segment %d" % seg.index)

# By Unit. Now we can calculate the PSTH averaged over trials for each unit:
for unit in block.list_units:
    stlist = [st - st.t_start for st in unit.spiketrains]
    count, bins = np.histogram(np.hstack(stlist))
    plt.figure()
    plt.bar(bins[:-1], count, width=bins[1] - bins[0])
    plt.title("PSTH of unit %s" % unit.name)
    
# By RecordingChannelGroup. Here we calculate a PSTH averaged over trials by 
# channel location, blending all units:
for rcg in block.recordingchannelgroups:
    stlist = []
    for unit in rcg.units:
        stlist.extend([st - st.t_start for st in unit.spiketrains])
    count, bins = np.histogram(np.hstack(stlist))
    plt.figure()
    plt.bar(bins[:-1], count, width=bins[1] - bins[0])
    plt.title("PSTH blend of tetrode %s" % rcg.name)
