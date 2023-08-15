import numpy as np
from sklearn.cluster import DBSCAN
import time
import consts
from calibrate import *

def get_packet_unique_id(packets):
    # unique id for each pixel, not to be confused with larnd-sim's pixel id
    unique_ids = ((((packets['io_group'].astype(int)) * 256 \
        + packets['io_channel'].astype(int)) * 256 \
        + packets['chip_id'].astype(int)) * 64 \
        + packets['channel_id'].astype(int)).astype(str)
    return unique_ids

def zip_pixel_tyz(packets, ts, mc_assn, pixel_xy, module, disabled_channel_IDs, detprop, pedestal_dict, config_dict):
    ## form zipped array using info from dictionary to use in clustering
    ## calculates first relative packet coordinates in each module, then adjust by TPC offsets
    ## some of this code copied from larnd-sim

    TPC_OFFSETS = np.array(detprop['tpc_offsets'])*10
    # Inverting x and z axes
    TPC_OFFSETS[:, [2, 0]] = TPC_OFFSETS[:, [0, 2]]

    module_to_io_groups = detprop['module_to_io_groups']
    io_groups = packets['io_group']
    io_groups_rel = np.copy(io_groups)
    io_groups_rel[io_groups_rel % 2 == 1] = 1
    io_groups_rel[io_groups_rel % 2 == 0] = 2

    """ test this as a replacement for the below code, has some issues
    # find indices of packets that are not in disabled channels list and is in the list of pixel keys
    pixel_xy_keys = np.array(list(pixel_xy.keys()))
    unique_ids = ((io_groups_rel.astype('i8') * 256 + packets['io_channel'].astype('i8')) * 256 + packets['chip_id'].astype('i8'))*64 + packets['channel_id'].astype('i8')
    packets_in_dict_mask = np.isin(unique_ids, pixel_xy_keys)
    packets_not_disabled_mask = np.invert(np.isin(unique_ids, disabled_channel_IDs))
    packets_keep_mask = packets_in_dict_mask & packets_not_disabled_mask
    packets_indices = np.where(packets_keep_mask)[0]
    
    txyz = np.zeros((len(packets_indices), 5))
    v_calib = np.zeros((len(packets_indices), 3))
    for i, index in enumerate(packets_indices):
        dict_values = pixel_xy.get(unique_ids[index])
        txyz[i] = np.array([v_drift*ts[index], dict_values[0], dict_values[1], dict_values[2], dict_values[3]])
        if mc_assn is None:
            v_calib[i] = np.array([pedestal_dict[unique_ids[index]]['pedestal_mv'], \
                                       config_dict[unique_ids[index]]['vcm_mv'], config_dict[unique_ids[index]]['vref_mv']])
        else:
            v_calib[i] = np.array([v_pedestal_sim, v_cm_sim, v_ref_sim])
    """
    
    xyz_values = []
    ts_inmm = []
    v_ped, v_cm, v_ref, unique_ids = [], [], [], []
    packets_keep_mask = np.zeros(len(packets), dtype=bool)
    for i in range(len(packets['io_channel'])):
        unique_id = ((io_groups_rel[i].astype('i8') * 256 + packets[i]['io_channel'].astype('i8')) * 256 + packets[i]['chip_id'].astype('i8'))*64 + packets[i]['channel_id'].astype('i8')

        io_group = io_groups_rel[i]
        io_channel = packets['io_channel'][i]
        chip_id = packets['chip_id'][i]
        channel_id = packets['channel_id'][i]
        unique_id = get_packet_unique_id(packets[i])

        dict_values = pixel_xy.get((io_group, io_channel, chip_id, channel_id))
        #dict_values = pixel_xy.get(unique_id)
        if dict_values is not None:
            if disabled_channel_IDs is not None and np.any(np.isin(disabled_channel_IDs, int(unique_id))):
                pass # pass if packet is from channel that is in the disabled channels list
            else:
                xyz_values.append([dict_values[0], dict_values[1], dict_values[2], dict_values[3]])
                ts_inmm.append(v_drift*1e1*ts[i]*0.1)
                packets_keep_mask[i] = True
                unique_ids.append(unique_id)
                if mc_assn is None:
                    v_ped.append(pedestal_dict[unique_id]['pedestal_mv'])
                    v_cm.append(config_dict[unique_id]['vcm_mv'])
                    v_ref.append(config_dict[unique_id]['vref_mv'])
                else:
                    v_ped.append(v_pedestal_sim)
                    v_cm.append(v_cm_sim)
                    v_ref.append(v_ref_sim)
        #else:
        #    print(f'KeyError {(packets[i]['io_group'], packets[i]['io_channel'], packets[i]['chip_id'], packets[i]['channel_id'])}')
    xyz_values = np.array(xyz_values)
    ts_inmm = np.array(ts_inmm)
    v_ped = np.array(v_ped)
    v_cm = np.array(v_cm)
    v_ref = np.array(v_ref)
    unique_ids = np.array(unique_ids)
    
    # adjust coordinates by TPC offsets, if there's >1 module
    io_group_grouped_by_module = list(module_to_io_groups.values())
    for i in range(len(io_group_grouped_by_module)):
        io_group_group = io_group_grouped_by_module[i]
        if len(np.unique(io_groups)) > 2:
            xyz_values[(io_groups == io_group_group[0]) | (io_groups == io_group_group[1])] += np.concatenate((TPC_OFFSETS[i], np.array([0])))
        else:
            pass
    
    txyz = np.hstack((ts_inmm[:, np.newaxis], xyz_values))
    return txyz, packets_keep_mask, v_ped, v_cm, v_ref, unique_ids
    #return txyz, packets_keep_mask, v_calib[:,0], v_calib[:,1], v_calib[:,2], unique_ids

def cluster_packets(eps,min_samples,txyz):
    ### Cluster packets into charge events
    # INPUT: DBSCAN parameters (eps: mm; min_samples: int), packet txyz list
    # OUTPUT: DBSCAN fit db.
    db = DBSCAN(eps=eps, min_samples=min_samples).fit(txyz) 
    return db

def getEventIDs(txyz, mc_assn, tracks, event_ids):
    for i in range(len(txyz)):
        index = int(mc_assn[i][0][0])
        tracks_index = tracks[index]
        event_id = tracks_index[consts.EVENT_SEPARATOR]
        event_ids[i] = event_id

def find_charge_clusters(labels,dataword,txyz,v_ref,v_cm,v_ped,unix,io_group,unique_ids, \
                                      hits_size, mc_assn, tracks):
    ### Make hits and clusters datasets from DBSCAN clusters and corresponding hits
    # Inputs: 
    #   labels: list of labels from DBSCAN
    #   dataword: packet ADC counts
    #   unique_ids: unique id for each pixel corresponding to the packets
    #   v_ref, v_cm, v_ped: arrays providing pixel parameters for ADC->ke- conversion
    #   ...
    # Outputs:
    #   clusters: array of cluster data
    #   hits: array of hit-level data
    indices_sorted = np.argsort(labels)
    labels = labels[indices_sorted]
    txyz = txyz[indices_sorted]
    v_ref = v_ref[indices_sorted]
    v_cm = v_cm[indices_sorted]
    v_ped = v_ped[indices_sorted]
    unix = unix[indices_sorted]
    io_group = io_group[indices_sorted]
    unique_ids = unique_ids[indices_sorted]
    dataword = dataword[indices_sorted]
    
    charge = adcs_to_mV(dataword, v_ref, v_cm, v_ped)
    q_vals = np.bincount(labels, weights=charge)
    
    # get event IDs if MC
    event_ids = np.zeros(len(txyz))
    if mc_assn is not None:
        getEventIDs(txyz, mc_assn, tracks, event_ids)
    else:
        event_ids = np.ones_like(len(txyz))*-1
    
    # add hits to hits dataset
    hits = np.zeros((len(labels),), dtype=consts.hits_dtype)
    hits['q'] = charge
    hits['io_group'] = io_group
    hits['t'] = (txyz[:,0]*mm_to_ns).astype('i8')
    hits['x'] = txyz[:,1]
    hits['y'] = txyz[:,2]
    hits['z_anode'] = txyz[:,3]
    hits['z_drift'] = txyz[:,4]
    hits['unique_id'] = unique_ids
    hits['unix'] = unix
    hits['cluster_index'] = labels + hits_size
    hits['event_id'] = event_ids
        
    label_indices = np.concatenate(([0], np.flatnonzero(labels[:-1] != labels[1:])+1, [len(labels)]))[1:-1]
    label_timestamps = np.split(txyz[:,0]*mm_to_ns, label_indices)
    label_x = np.split(txyz[:,1], label_indices)
    label_y = np.split(txyz[:,2], label_indices)
    label_z = np.split(txyz[:,3], label_indices)
    
    min_timestamps = np.array(list(map(np.min, label_timestamps)), dtype='i8')
    max_timestamps = np.array(list(map(np.max, label_timestamps)), dtype='i8')
    
    # save array of event information
    n_vals = np.bincount(labels)
    n_vals_mask = n_vals != 0
    io_group_vals = np.bincount(labels, weights=io_group)[n_vals_mask]
    unix_vals = np.bincount(labels, weights=unix)[n_vals_mask]
    q_vals = q_vals[n_vals_mask]
    n_vals = n_vals[n_vals_mask] # get rid of n_vals that are 0, otherwise get divide by 0 later
    
    x_min = np.array(list(map(np.min, label_x)))
    x_max = np.array(list(map(np.max, label_x)))
    y_min = np.array(list(map(np.min, label_y)))
    y_max = np.array(list(map(np.max, label_y)))
    z_min = np.array(list(map(np.min, label_z)))
    z_max = np.array(list(map(np.max, label_z)))
    
    clusters = np.zeros((len(n_vals),), dtype=consts.clusters_dtype)
    clusters['nhit'] = n_vals
    clusters['q'] = q_vals
    clusters['unix'] = (unix_vals/n_vals).astype('i8') # all of these hits should have the same unix anyway
    clusters['io_group'] = (io_group_vals/n_vals).astype('i4')
    clusters['t_min'] = min_timestamps
    clusters['t_mid'] = ((min_timestamps + max_timestamps)/2).astype('i8')
    clusters['t_max'] = max_timestamps
    clusters['x_min'] = x_min
    clusters['x_max'] = x_max
    clusters['x_mid'] = (x_min + x_max)/2
    clusters['y_min'] = y_min
    clusters['y_mid'] = (y_min + y_max)/2
    clusters['y_max'] = y_max
    clusters['z_min'] = z_min
    clusters['z_mid'] = (z_min + z_max)/2
    clusters['z_max'] = z_max
    clusters['ext_trig_index'] = np.ones(len(n_vals), dtype='i4')*-1
    return clusters, hits

def analysis(packets, pixel_xy, mc_assn, tracks, module, hits_max_cindex, \
             disabled_channel_IDs, detprop, pedestal_dict, config_dict):
    ## do charge reconstruction
    clusters = np.zeros((0,), dtype=consts.clusters_dtype)
    hits = np.zeros((0,), dtype=consts.hits_dtype)
    
    start = time.time()
    pkt_7_mask = packets['packet_type'] == 7
    pkt_4_mask = packets['packet_type'] == 4
    pkt_0_mask = packets['packet_type'] == 0
    make_packet_type_masks = time.time() - start
    
    start = time.time()
    # grab the PPS timestamps of pkt type 7s and correct for PACMAN clock drift
    PPS_pt7 = PACMAN_drift(packets, module)[pkt_7_mask].astype('i8')*1e-1*1e3 # ns
    io_group_pt7 = packets[pkt_7_mask]['io_group']
    # assign a unix timestamp to each packet based on the timestamp of the previous packet type 4
    unix_timestamps = np.copy(packets['timestamp']).astype('i8')
    unix_timestamps[np.invert(pkt_4_mask)] = 0
    nonzero_indices = np.nonzero(unix_timestamps)[0]
    unix_timestamps = np.interp(np.arange(len(unix_timestamps)), nonzero_indices, unix_timestamps[nonzero_indices])
    unix_pt7 = np.copy(unix_timestamps)[pkt_7_mask].astype('i8')
    unix = np.copy(unix_timestamps)[pkt_0_mask].astype('i8')
    get_PPS_unix_times = time.time() - start
    
    start = time.time()
    # match together external triggers corresponding to single light triggers
    threshold = 500
    differences = PPS_pt7[:, None] - PPS_pt7
    mask = np.abs(differences) < threshold
    mask = mask * np.tri(*mask.shape, k=-1)
    i, j = np.where(mask)
    
    PPS_matched, unix_matched = [], [] # add eventually a module identifier
    # loop through matched ext triggers and make single arrays for PPS and unix timestamps
    for x, y in zip(i,j):
        if unix_pt7[x] == unix_pt7[y]:
            PPS_matched.append(int((float(PPS_pt7[x]) + float(PPS_pt7[y]))/2))
            unix_matched.append(unix_pt7[x])
            
    ext_trig = np.zeros((np.size(PPS_matched),), dtype=consts.ext_trig_dtype)
    ext_trig['unix'] = np.array(unix_matched).astype('i8')
    ext_trig['t'] = np.array(PPS_matched).astype('i8')
    match_ext_triggers = time.time() - start
    
    start = time.time()
    # apply a few PPS timestamp corrections, and select only data packets for analysis
    ts, packets, mc_assn, unix = timestamp_corrector(packets, mc_assn, unix, module)
    ts_corrector_time = time.time() - start
    
    start = time.time()
    # zip up x, y, z, and t values for clustering
    txyz, packets_keep_mask, v_ped, v_cm, v_ref, unique_ids = zip_pixel_tyz(packets, ts, mc_assn, pixel_xy, module, \
                                        disabled_channel_IDs, detprop, pedestal_dict, config_dict)
    zip_time = time.time() - start
    
    # remove packets with key errors
    packets = packets[packets_keep_mask]
    unix = unix[packets_keep_mask]
    
    if mc_assn is not None:
        mc_assn = mc_assn[packets_keep_mask]

    start = time.time()
    db = cluster_packets(eps, min_samples, txyz[:,0:4])
    dbscan_time = time.time() - start
    
    labels = np.array(db.labels_)
    
    start = time.time()
    dataword = np.copy(packets['dataword'])
    io_group = np.copy(packets['io_group'])
    if np.size(labels) > 0:
        clusters, hits = \
            find_charge_clusters(labels,dataword,txyz,\
            v_ref=v_ref,v_cm=v_cm,v_ped=v_ped,\
            unix=unix, io_group=io_group,\
            unique_ids=unique_ids,\
            hits_size=hits_max_cindex,\
            mc_assn=mc_assn, tracks=tracks)
    find_charge_clusters_time = time.time() - start
    
    benchmarks = {'make_packet_type_masks': make_packet_type_masks, \
                 'get_PPS_unix_times': get_PPS_unix_times, \
                 'match_ext_triggers': match_ext_triggers, \
                 'zip_time': zip_time, 'dbscan_time': dbscan_time, \
                 'find_charge_clusters_time': find_charge_clusters_time}
    return clusters, ext_trig, hits, benchmarks
