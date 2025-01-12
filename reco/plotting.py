#!/usr/bin/env python
import matplotlib.pyplot as plt
import numpy as np
import h5py
import matplotlib.colors as colors
from matplotlib.colors import LogNorm
from tqdm import tqdm
from scipy import stats
import matplotlib.colors as mcolors
from math import ceil
import pandas as pd

def XY_Hist2D(clusters, figTitle=None, vmin=1e0, vmax=1e3, use_z_cut=True, isSingleCube=False, imageFileName=None, isHits=False, bins=None, hist_range=None):
    ### plot 2D histogram of clusters
    if isSingleCube:
        y_min_max = [-155,155]
        x_min_max = [-155,155]
        x_bins = 70
        y_bins = x_bins
        ncols=1
    else:
        if bins is not None:
            x_bins = bins[0]
            y_bins = bins[1]
        else:
            x_bins=140
            y_bins=2*x_bins
            
        if hist_range is not None:
            x_min_max = hist_range[0]
            y_min_max = hist_range[1]
        else:
            x_min_max = [-310,310]
            y_min_max = [-620,620]
            
        ncols=2
    fig, axes = plt.subplots(nrows=1, ncols=ncols, sharex=False, sharey=False, figsize=(8,6))
    cmap = plt.cm.jet
    z_anode_max = np.max(clusters['z_anode'])
    z_anode_min = np.min(clusters['z_anode'])
    if isSingleCube:
        H1 = axes.hist2d(clusters['x_mid'], clusters['y_mid'], range=[x_min_max, y_min_max],bins = [x_bins,y_bins], weights=np.ones_like(clusters['x_mid']),norm = colors.LogNorm(vmin=vmin,vmax=vmax))
        fig.colorbar(H1[3], ax=axes)
        
        #axes[0].set_title(f'TPC 1')
        fig.suptitle(figTitle, fontsize=10)
        axes.set_xlabel(r'pixel x [mm]')
        axes.set_ylabel(r'pixel y [mm]')
        axes.set_ylim(y_min_max[0], y_min_max[1])
        axes.set_xlim(x_min_max[0], x_min_max[1])
    else:
        if not use_z_cut:
            TPC1_mask = (clusters['z_anode'] < 0)
            TPC2_mask = (clusters['z_anode'] > 0)
        else:
            TPC1_mask = (clusters['z_anode'] < 0) & (clusters['z_drift_mid'] > z_anode_min) & (clusters['z_drift_mid'] < 0)
            TPC2_mask = (clusters['z_anode'] > 0) & (clusters['z_drift_mid'] < z_anode_max) & (clusters['z_drift_mid'] > 0)
        
        if isHits:
            H1 = axes[0].hist2d(clusters['x'][TPC1_mask], clusters['y'][TPC1_mask], range=[x_min_max, y_min_max],bins = [x_bins,y_bins], weights=np.ones_like(clusters['x'][TPC1_mask]),norm = colors.LogNorm(vmin=vmin,vmax=vmax))
            fig.colorbar(H1[3], ax=axes[0])
            H2 = axes[1].hist2d(clusters['x'][TPC2_mask], clusters['y'][TPC2_mask], range=[x_min_max, y_min_max], bins = [x_bins,y_bins], weights=np.ones_like(clusters['x'][TPC2_mask]),norm = colors.LogNorm(vmin=vmin,vmax=vmax))
        else:
            H1 = axes[0].hist2d(clusters['x_mid'][TPC1_mask], clusters['y_mid'][TPC1_mask], range=[x_min_max, y_min_max],bins = [x_bins,y_bins], weights=np.ones_like(clusters['x_mid'][TPC1_mask]),norm = colors.LogNorm(vmin=vmin,vmax=vmax))
            fig.colorbar(H1[3], ax=axes[0])
            H2 = axes[1].hist2d(clusters['x_mid'][TPC2_mask], clusters['y_mid'][TPC2_mask], range=[x_min_max, y_min_max], bins = [x_bins,y_bins], weights=np.ones_like(clusters['x_mid'][TPC2_mask]),norm = colors.LogNorm(vmin=vmin,vmax=vmax))
        
        fig.colorbar(H2[3], ax=axes[1])
        axes[0].set_title(f'TPC 1')
        axes[1].set_title(f'TPC 2')
        fig.suptitle(figTitle, fontsize=10)
        axes[0].set_xlabel(r'pixel x [mm]')
        axes[1].set_xlabel(r'pixel x [mm]')
        axes[0].set_ylabel(r'pixel y [mm]')
        axes[0].set_ylim(y_min_max[0], y_min_max[1])
        axes[0].set_xlim(x_min_max[0], x_min_max[1])
        axes[1].set_ylim(y_min_max[0], y_min_max[1])
        axes[1].set_xlim(x_min_max[0], x_min_max[1])
    if imageFileName is not None:
        plt.savefig(imageFileName)
    plt.show()

def XZ_Hist2D(clusters, figTitle=None, logYscale=False, vmin=1, vmax=1e3, weight_type=None, imageFileName=None, bins=None):
    ### plot 2D histogram of clusters
    x_min_max = [-310,310]
    if bins is not None:
        x_bins = bins
        y_bins = bins
    else:
        x_bins = 140
        y_bins = x_bins
    fig, axes = plt.subplots(nrows=1, ncols=1, sharex=False, sharey=False, figsize=(9,6))
    cmap = plt.cm.jet
    
    z_anode_max = np.max(clusters['z_anode'])
    z_anode_min = np.min(clusters['z_anode'])
    
    if logYscale:
        norm = colors.LogNorm(vmin=vmin,vmax=vmax)
    else:
        norm = None
    
    TPC1_mask = (clusters['z_anode'] < 0) & (clusters['z_drift_mid'] > z_anode_min) & (clusters['z_drift_mid'] < 0)
    TPC2_mask = (clusters['z_anode'] > 0) & (clusters['z_drift_mid'] < z_anode_max) & (clusters['z_drift_mid'] > 0)
    clusters_TPC1 = clusters[TPC1_mask]
    clusters_TPC2 = clusters[TPC2_mask]
    clusters_fiducial = np.concatenate((clusters_TPC1, clusters_TPC2))
    if weight_type == 'q':
        bin_counts = np.histogram2d(clusters_tagged['x_mid'], clusters_tagged['y_mid'], bins=[x_bins,y_bins], range=[x_min_max,x_min_max])[0]
        weights = clusters_fiducial['q']*221*1e-3
    else:
        weights = np.ones_like(clusters_fiducial['x_mid'])
    H1 = axes.hist2d(clusters_fiducial['x_mid'], clusters_fiducial['z_drift_mid'], \
                     range=[x_min_max,x_min_max],bins = [x_bins,y_bins], \
                     weights=weights, vmin=vmin, vmax=vmax,norm = norm)
    fig.colorbar(H1[3], ax=axes)
    axes.set_xlabel(r'z_{reco} [mm]')
    axes.set_ylabel(r'x_{drift} [mm]')
    axes.set_ylim(x_min_max[0], x_min_max[1])
    axes.set_xlim(x_min_max[0], x_min_max[1])
    fig.suptitle(figTitle)
    if imageFileName is not None:
        plt.savefig(imageFileName)
    plt.show()

def ZY_Hist2D(clusters, figTitle=None, vmin=1, vmax=1e3, imageFileName=None, use_z_cut=True, bins=None):
    if bins is not None:
        x_bins = bins[0]
        y_bins = bins[1]
    else:
        x_bins = 140
        y_bins = x_bins
    z_anode_max = np.max(clusters['z_anode'])
    z_anode_min = np.min(clusters['z_anode'])
    if not use_z_cut:
        TPC1_mask = (clusters['z_anode'] < 0)
        TPC2_mask = (clusters['z_anode'] > 0)
    else:
        TPC1_mask = (clusters['z_anode'] < 0) & (clusters['z_drift_mid'] > z_anode_min) & (clusters['z_drift_mid'] < 0)
        TPC2_mask = (clusters['z_anode'] > 0) & (clusters['z_drift_mid'] < z_anode_max) & (clusters['z_drift_mid'] > 0)

    mask = TPC1_mask | TPC2_mask
    x_mid_io1 = clusters[mask][clusters[mask]['io_group'] == 1]['x_mid']
    x_mid_io2 = clusters[mask][clusters[mask]['io_group'] == 2]['x_mid']
    y_mid_io1 = clusters[mask][clusters[mask]['io_group'] == 1]['y_mid']
    y_mid_io2 = clusters[mask][clusters[mask]['io_group'] == 2]['y_mid']
    z_drift_mid_io1 = clusters[mask][clusters[mask]['io_group'] == 1]['z_drift_mid']
    z_drift_mid_io2 = clusters[mask][clusters[mask]['io_group'] == 2]['z_drift_mid']
    
    pos_x_mask = (x_mid_io1 > 0)
    neg_x_mask = (x_mid_io1 < 0)

    y_mid_io1_pos_x = y_mid_io1[x_mid_io1 > 0]
    y_mid_io1_neg_x = y_mid_io1[x_mid_io1 < 0]
    y_mid_io2_pos_x = y_mid_io2[x_mid_io2 > 0]
    y_mid_io2_neg_x = y_mid_io2[x_mid_io2 < 0]
    z_drift_mid_io1_pos_x = z_drift_mid_io1[x_mid_io1 > 0]
    z_drift_mid_io1_neg_x = z_drift_mid_io1[x_mid_io1 < 0]
    z_drift_mid_io2_pos_x = z_drift_mid_io2[x_mid_io2 > 0]
    z_drift_mid_io2_neg_x = z_drift_mid_io2[x_mid_io2 < 0]

    y_mid_pos_x = np.concatenate((y_mid_io1_pos_x, y_mid_io2_pos_x))
    y_mid_neg_x = np.concatenate((y_mid_io1_neg_x, y_mid_io2_neg_x))
    z_drift_mid_pos_x = np.concatenate((z_drift_mid_io1_pos_x, z_drift_mid_io2_pos_x))
    z_drift_mid_neg_x = np.concatenate((z_drift_mid_io1_neg_x, z_drift_mid_io2_neg_x))

    y_min_max = [-620,620]
    x_min_max = [-310,0]
    #x_bins = 140
    #y_bins = 2*x_bins
    fig, axes = plt.subplots(nrows=1, ncols=2, sharex=False, sharey=False, figsize=(8,6))
    cmap = plt.cm.jet

    H1 = axes[0].hist2d(z_drift_mid_pos_x, y_mid_pos_x, range=[[-310, 310], [-620, 620]],bins = [x_bins,y_bins], weights=np.ones_like(y_mid_pos_x),norm = colors.LogNorm(vmin=vmin,vmax=vmax))
    fig.colorbar(H1[3], ax=axes[0])
    H2 = axes[1].hist2d(z_drift_mid_neg_x, y_mid_neg_x, range=[[-310, 310], [-620, 620]], bins = [x_bins,y_bins], weights=np.ones_like(y_mid_neg_x),norm = colors.LogNorm(vmin=vmin,vmax=vmax))
    fig.colorbar(H2[3], ax=axes[1])
    axes[0].set_xlabel(r'Reconstructed Drift Coordinate [mm]')
    axes[1].set_xlabel(r'Reconstructed Drift Coordinate [mm]')
    axes[0].set_ylabel(r'pixel y [mm]')
    #axes[0].set_ylim(y_min_max[0], y_min_max[1])
    #axes[0].set_xlim(x_min_max[0], x_min_max[1])
    #axes[1].set_ylim(y_min_max[0], y_min_max[1])
    #axes[1].set_xlim(x_min_max[0], x_min_max[1])
    fig.suptitle(figTitle)
    if imageFileName is not None:
        plt.savefig(imageFileName)
    plt.show()
    
def plot_2D_statistic(clusters, values, stat, plot_type, xlabel=None, ylabel=None, figTitle=None, vmin=None, vmax=None, log_scale=False, isSingleCube=False, imageFileName=None, isNotClusters=False):
    if plot_type == 'xy':
        if isSingleCube:
            ncols=1
            figsize=(8,6)
        else:
            ncols=2
            figsize=(8,6)
    elif plot_type == 'xz':
        ncols=1
        figsize=(8,6)
    elif plot_type == 'zy':
        ncols=2
        figsize=(8,6)
    else:
        raise Exception('plot type not supported')
    fig, axes = plt.subplots(nrows=1, ncols=ncols, sharex=False, sharey=False, figsize=figsize)
    cmap = plt.cm.jet
        
    if plot_type == 'xz':
        RANGE = [-310,310]
        x_bins = 140
        y_bins = x_bins
        axes.set_xlabel(r'$x_{reco}$ [mm]')
        axes.set_ylabel(r'$z_{reco}$ [mm]')
        axes.set_ylim(RANGE[0], RANGE[1])
        axes.set_xlim(RANGE[0], RANGE[1])
    elif plot_type == 'xy':
        if isSingleCube:
            y_min_max = [-155,155]
            x_min_max = [-155,155]
            RANGE=[x_min_max, y_min_max]
            x_bins = 70
            y_bins = x_bins
            axes.set_xlabel(r'$x_{reco}$ [mm]')
            axes.set_ylabel(r'$y_{reco}$ [mm]')
            axes.set_ylim(y_min_max[0], y_min_max[1])
            axes.set_xlim(x_min_max[0], x_min_max[1])
        else:
            y_min_max = [-620,620]
            x_min_max = [-310,310]
            RANGE=[x_min_max, y_min_max]
            x_bins = 140
            y_bins = 2*x_bins
            axes[0].set_xlabel(r'$x_{reco}$ [mm]')
            axes[1].set_xlabel(r'$x_{reco}$ [mm]')
            axes[0].set_ylabel(r'$y_{reco}$ [mm]')
            axes[0].set_ylim(y_min_max[0], y_min_max[1])
            axes[0].set_xlim(x_min_max[0], x_min_max[1])
            axes[1].set_ylim(y_min_max[0], y_min_max[1])
            axes[1].set_xlim(x_min_max[0], x_min_max[1])
    elif plot_type == 'zy':
        y_min_max = [-620,620]
        x_min_max = [-310,310]
        RANGE=[x_min_max, y_min_max]
        x_bins = 140
        y_bins = 2*x_bins
        axes[0].set_xlabel(r'$z_{reco}$ [mm]')
        axes[1].set_xlabel(r'$z_{reco}$ [mm]')
        axes[0].set_ylabel(r'$y_{reco}$ [mm]')
        axes[0].set_ylim(y_min_max[0], y_min_max[1])
        axes[0].set_xlim(x_min_max[0], x_min_max[1])
        axes[1].set_ylim(y_min_max[0], y_min_max[1])
        axes[1].set_xlim(x_min_max[0], x_min_max[1])
    if plot_type == 'xy':
        x = clusters['x_mid']
        y = clusters['y_mid']
        hist_data = stats.binned_statistic_2d(x, y, values, statistic=stat, bins=[x_bins,y_bins], range=RANGE)
    elif plot_type == 'zy':
        x = clusters['z_drift_mid']
        y = clusters['y_mid']
        hist_data = stats.binned_statistic_2d(x, y, values, statistic=stat, bins=[x_bins,y_bins], range=RANGE)
    elif plot_type == 'xz':
        x = clusters['x_mid']
        y = clusters['z_drift_mid']
        hist_data = stats.binned_statistic_2d(x, y, values, statistic=stat, bins=[x_bins,y_bins], range=[RANGE, RANGE])

    if log_scale:
        norm = mcolors.LogNorm(vmin=np.nanmin(hist_data.statistic), vmax=np.nanmax(hist_data.statistic))
    else:
        norm = None
    if plot_type == 'xz':
        im = axes.imshow(hist_data.statistic.T, cmap=cmap,norm=norm, origin='lower', extent=[RANGE[0], RANGE[1], RANGE[0], RANGE[1]])
        colorbar = plt.colorbar(im, ax=axes)
        im.set_clim(vmin, vmax)
    elif plot_type == 'zy':
        im = axes[0].imshow(hist_data.statistic.T, cmap=cmap,norm=norm, origin='lower', extent=[RANGE[0][0], RANGE[0][1], RANGE[1][0], RANGE[1][1]])
        im.set_clim(vmin, vmax)
        im = axes[1].imshow(hist_data.statistic.T, cmap=cmap, norm=norm, origin='lower', extent=[RANGE[0][0], RANGE[0][1], RANGE[1][0], RANGE[1][1]])
        colorbar = plt.colorbar(im, ax=axes)
        im.set_clim(vmin, vmax)
    elif plot_type == 'xy':
        if isSingleCube:
            im = axes.imshow(hist_data.statistic.T, cmap=cmap,norm=norm, origin='lower', extent=[RANGE[0][0], RANGE[0][1], RANGE[1][0], RANGE[1][1]])
            im.set_clim(vmin, vmax)
        else:
            im = axes[0].imshow(hist_data.statistic.T, cmap=cmap,norm=norm, origin='lower', extent=[RANGE[0][0], RANGE[0][1], RANGE[1][0], RANGE[1][1]])
            im.set_clim(vmin, vmax)
            im = axes[1].imshow(hist_data.statistic.T, cmap=cmap, norm=norm, origin='lower', extent=[RANGE[0][0], RANGE[0][1], RANGE[1][0], RANGE[1][1]])
        colorbar = plt.colorbar(im, ax=axes)
        im.set_clim(vmin, vmax)
    fig.suptitle(figTitle)
    if imageFileName is not None:
        plt.savefig(imageFileName)
    plt.show()
    

def make_hist(array, bins, range_start, range_end):
    ### make histogram of charge
    
    # get histogram data
    bin_contents,binEdges = np.histogram(np.array(array),bins=bins,range=(range_start,range_end))
    bincenters = 0.5*(binEdges[1:]+binEdges[:-1])
    error      = np.sqrt(bin_contents)
    
    return bincenters, bin_contents, error

def get_hist_data(clusters, bins, data_type, calibrate=False, binwidth=None, recomb_filename=None, bin_start=0, DET=None, is_adcs=False):
    ### set bin size and histogram range, correct for recombination using NEST, return histogram parameters
    # INPUT: `the_data` is a 1D numpy array of charge cluster charge values (mV)
    #        `bins` is the number of bins to use (this effectively sets the range, the binsize is constant w.r.t. bins)
    #        `data_type` is either `data` for real data or `MC` for simulation
    #        `calibrate` is either True or False, if True will use NEST to correct for recombination
    #        `norm` sets the normalization of histogram. Options are `area` and `max`, otherwise `None`
    #        `binwidth` is optional to specify binwidth. Otherwise will be 2*LSB by default
    #        `recomb_filename` is path to h5 file containing electron recombination values as a function of energy
    
    v_cm_sim = 288.28125
    v_ref_sim = 1300.78125
    v_pedestal_sim = 580
    
    v_cm_data = 288.28125
    v_ref_data = 1300.78125
    if DET == 'module0_run1' or DET == 'module0_run2':
        v_cm_data = 288.28125
        v_ref_data = 1300.78125
    elif DET == 'module1':
        v_cm_data = 284.27734375
        v_ref_data = 1282.71484375
    elif DET == 'module2' or DET == 'module3':
        v_cm_data = 478.125
        v_ref_data = 1567.96875
    else:
        v_cm_data = 288.28125
        v_ref_data = 1300.78125 
    
    gain_data = 1/221
    gain_sim = 1/221
    if is_adcs:
        data = np.copy(clusters['adcs'])
    else:
        data = np.copy(clusters['q'])
    
    # set parameters for data or MC for determining bin size
    vcm_mv = v_cm_data
    vref_mv = v_ref_data
    gain = gain_data
    
    if data_type == 'MC':
        vcm_mv = v_cm_sim
        vref_mv = v_ref_sim
        gain = gain_sim
    LSB = (vref_mv - vcm_mv)/256
    
    if calibrate:
        if is_adcs:  
            data = data/gain * 1e-3 * LSB
        else:
            data = data/gain * 1e-3
    
    if calibrate:
        if is_adcs:
            width = LSB / gain * 1e-3 * LSB
        else:
            width = LSB / gain * 1e-3
    else:
        width = LSB
    
    # add small +/- offset in MC for fix binning issues
    offset = np.zeros_like(data)
    if data_type == 'MC' or data_type == 'data':
        MC_size = len(data)
        offset = stats.uniform.rvs(loc=0, scale=1, size=MC_size)*width*np.random.choice([-0.5,0.5], size=MC_size, p=[.5, .5])
        data += offset
    if binwidth is not None:
        width = binwidth
    
    range_start = width*bin_start # ke-
    range_end = width*(bins+bin_start)
    # if converting to energy, use NEST model
    eV_per_e = 1
    if recomb_filename is not None:
        eV_per_e = 23.6
        recomb_file = h5py.File(recomb_filename)
        energies = np.array(recomb_file['NEST']['E_start'])
        recombination = np.array(recomb_file['NEST']['R'])
        charge_ke = energies / 23.6 * recombination
        values = np.interp(data, charge_ke, recombination)
        data = data/values
    
    # get histogram parameters
    nbins = int(bins/2)
    bin_centers, bin_contents, bin_error = make_hist(data*eV_per_e, nbins, range_start*eV_per_e,range_end*eV_per_e)
    return bin_centers, bin_contents, bin_error

def plotRecoSpectrum(clusters, nbins=100, data_type='data', color='b', linewidth=1, label=None, linestyle=None, norm=None,plot_errorbars=False, useYlog=False,calibrate=True, bin_start=0, axes=None, recomb_filename=None, DET=None, figTitle=None, imageFileName=None, is_adcs=False):
    ### plot reco spectrum
    if axes is None:
        fig, axes = plt.subplots(nrows=1, ncols=1, sharex=False, sharey=False, figsize=(6,4))
    bin_centers, bin_contents, bin_error = get_hist_data(clusters, nbins, data_type, calibrate=calibrate, bin_start=bin_start, recomb_filename=recomb_filename, DET=DET, is_adcs=is_adcs)
    if norm == 'area':
        total_bin_contents = np.sum(bin_contents)
        bin_contents = bin_contents / total_bin_contents
        bin_error = bin_error / total_bin_contents
        axes.set_ylabel('bin count / total bin count')
    elif norm == 'max':
        max_bin_content = np.max(bin_contents)
        bin_contents = bin_contents / max_bin_content
        bin_error = bin_error / max_bin_content
        axes.set_ylabel('bin count / max bin count')
    else:
        axes.set_ylabel('bin count')
    if calibrate and recomb_filename is None:
        axes.set_xlabel('Cluster Charge [ke-]')
    elif not calibrate and recomb_filename is None:
        axes.set_xlabel('Cluster Charge [mV]')
    elif calibrate and recomb_filename is not None:
        axes.set_xlabel('Cluster Energy [keV]')
    axes.step(bin_centers, bin_contents, linewidth=linewidth, color=color,linestyle=linestyle, where='mid',alpha=0.7, label=label)
    if useYlog:
        axes.set_yscale('log')
    if plot_errorbars:
        axes.errorbar(bin_centers, bin_contents, yerr=bin_error,color='k',fmt='o',markersize = 1)
    if imageFileName is not None:
        plt.savefig(imageFileName)
    return bin_contents

def proximity_cut(clusters_chunk, tile_position, tpc_id, opt_cut_shape, d, ellipse_b):
    cluster_in_shape = np.zeros(len(clusters_chunk), dtype=bool)
    hit_to_clusters_dist = np.sqrt((clusters_chunk['x_mid'] - tile_position[0])**2 + \
                                   (clusters_chunk['y_mid'] - tile_position[1])**2)
    # can add additional optical cut shapes here as addition elif statements
    if opt_cut_shape == 'circle':
        cluster_in_shape = (hit_to_clusters_dist < d) \
        & (np.abs(clusters_chunk['x_mid']) < 315) \
        & (np.abs(clusters_chunk['y_mid']) < 630) \
        & (clusters_chunk['io_group'] == tpc_id)
    elif opt_cut_shape == 'ellipse':
        cluster_in_shape = (is_point_inside_ellipse(clusters_chunk['x_mid'], clusters_chunk['y_mid'],tile_position[0], tile_position[1], d, ellipse_b)) & (clusters_chunk['io_group'] == tpc_id)
    elif opt_cut_shape == 'rect':
        if tile_position[0] < 0:
            cluster_in_shape = (clusters_chunk['x_mid'] < tile_position[0]+d) \
                & (clusters_chunk['y_mid'] > tile_position[1]-304/2) \
                & (clusters_chunk['y_mid'] < tile_position[1]+304/2) \
                & (clusters_chunk['io_group'] == tpc_id)
        elif tile_position[0] > 0:
            cluster_in_shape = (clusters_chunk['x_mid'] > tile_position[0]-d) \
                & (clusters_chunk['y_mid'] > tile_position[1]-304/2) \
                & (clusters_chunk['y_mid'] < tile_position[1]+304/2) \
                & (clusters_chunk['io_group'] == tpc_id)
    else:
        raise ValueError('shape not supported')
    return cluster_in_shape

def corner_cut(clusters, tolerance, special_cases=None):
    # inputs: clusters; clusters array to apply corner cut on
    #         tolerance; distance in mm away from corner to cut clusters in any direction
    #         special_cases (optional); extra points to apply corner cut on, for instance when there are disabled tiles and
    #                       need to cut extra cosmic clippers. This is a dictionary where the key is either 'xy', 'xz', or 'zy',
    #                       and the value is a list or tuple of two values being the point to apply cut on in the corresponding
    #                       view. 
    # outputs: mask to apply to clusters to remove clusters near corners.
    pos_names = {'xy': ['x_mid', 'y_mid'], 'xz': ['x_mid', 'z_drift_mid'], 'zy': ['z_drift_mid', 'y_mid']}
    x_edge, y_edge, z_edge = 305, 615, 305
    signs = [(-1,-1), (-1,1), (1,1), (1,-1)]
    overall_mask = np.ones(len(clusters), dtype=bool)
    for dims in ['xy', 'xz', 'zy']:
        pos_name_list = pos_names[dims]
        if dims == 'xy':
            xlim, ylim = x_edge, y_edge
        elif dims == 'xz':
            xlim, ylim = x_edge, z_edge
            #continue
        elif dims == 'zy':
            xlim, ylim = z_edge, y_edge
            #continue
        for sign in signs:
            dist = np.sqrt((clusters[pos_name_list[0]] - sign[0]*xlim)**2 + (clusters[pos_name_list[1]] - sign[1]*ylim)**2)
            overall_mask = overall_mask & (dist > tolerance)
        if special_cases is not None:
            for dim in special_cases.keys():
                xlim, ylim, side = special_cases[dim][0], special_cases[dim][1], special_cases[dim][2]
                if dim == 'xy':
                    dist = np.sqrt((clusters['x_mid'] - xlim)**2 + (clusters['y_mid'] - ylim)**2)
                elif dim == 'xz':
                    dist = np.sqrt((clusters['x_mid'] - xlim)**2 + (clusters['z_drift_mid'] - ylim)**2)
                elif dim == 'zy':
                    dist = np.sqrt((clusters['z_drift_mid'] - xlim)**2 + (clusters['y_mid'] - ylim)**2)
                if side == 'left' and dim == 'zy':
                    side_mask = clusters['x_mid'] < 0
                elif side == 'right' and dim == 'zy':
                    side_mask = clusters['x_mid'] > 0
                if side == 'left' and dim == 'xy':
                    side_mask = clusters['io_group'] == 2
                elif side == 'right' and dim == 'xy':
                    side_mask = clusters['io_group'] == 1
                overall_mask = overall_mask & ((dist > tolerance) | side_mask)
    return overall_mask
        
def f90_cut(clusters, light_hits):
    # apply f90 cut to try to isolate alphas
    indices = []
    all_f90_values = []
    for i in range(len(light_hits['samples'])):
        samples = light_hits['samples'][i]
        samples = samples - np.mean(samples[40:70])
        
        df = pd.DataFrame({'wvfm': samples})    
        # Apply rolling average
        samples = df['wvfm'].rolling(window=2).mean()
    
        # sometimes the pulse starts early; cut these since there are not that many.
        if np.mean(samples[0:70]) < -50:
            continue
        start_point = 72 # ticks
        window = 6
        end_point = start_point + int(7000/16)
        integral_small = np.trapz(samples[start_point:start_point+window+1], dx=16)
        integral_large = np.trapz(samples[start_point:end_point], dx=16)
        f90 = integral_small/integral_large
        
        if f90 > 0.6 and f90 < 0.8:
            indices.append(i)
        all_f90_values.append(f90)
    indices = np.array(indices)
    print(f'{len(indices)} alpha-like events')
    return clusters[np.isin(clusters['light_trig_index'][:,0], indices)], indices, all_f90_values

def is_point_inside_ellipse(x, y, h, k, a, b):
    """
    Check if a point (x, y) is inside an ellipse centered at (h, k) with semi-axes a and b.
    This is used to determine if a cluster is within an ellipse relative to the middle 
    of a photon detector tile. 

    Parameters:
        x (float): x-coordinate of the point to check.
        y (float): y-coordinate of the point to check.
        h (float): x-coordinate of the ellipse's center.
        k (float): y-coordinate of the ellipse's center.
        a (float): Length of the semi-major axis of the ellipse.
        b (float): Length of the semi-minor axis of the ellipse.

    Returns:
        bool: True if the point is inside the ellipse, False otherwise.
    """
    return ((x - h)**2 / a**2) + ((y - k)**2 / b**2) <= 1

def apply_cuts(f, shape, d, ellipse_b, corner_tolerance, use_proximity_cut=True, use_f90_cut=False, use_corner_cut=True,special_cases=None):
    ### apply data cuts, including proximity cut and corner/edge cut
    clusters = np.array(f['clusters'])[(f['clusters']['light_trig_index'] != -1).sum(axis=1) == 1]
    light_trig_indices = np.unique(clusters['light_trig_index'][:,0])
    light_hits_summed = np.array(f['light_hits_summed'])
    
    f90_values = []
    if use_f90_cut:
        clusters, light_trig_indices, f90_values = f90_cut(clusters, light_hits_summed)
    
    light_matches = {'amplitudes':[], 'x':[], 'y':[], 'z':[], 'q':[], 'io_group':[], 'nhit':[], 'tile_x':[], 'tile_y':[], 'det_type':[], 't0':[], 't':[], 'unix':[]}
    
    if use_proximity_cut:
        clusters_mask = np.zeros(len(clusters), dtype=bool)
        for light_index in light_trig_indices:
            light_hits = light_hits_summed[light_hits_summed['light_trig_index'] == light_index]
            for light_hit in light_hits:
                tpc_id = light_hit['io_group']
                tile_position = (light_hit['tile_x'], light_hit['tile_y'])
                clusters_event_mask = clusters['light_trig_index'][:,0] == light_index
                clusters_event = clusters[clusters_event_mask]
                clusters_chunk_mask = proximity_cut(clusters_event, tile_position, tpc_id, shape, d, ellipse_b)
                
                if use_corner_cut:
                    clusters_chunk_mask = clusters_chunk_mask & corner_cut(clusters_event, corner_tolerance, special_cases)

                if np.sum(clusters_chunk_mask) == 1:
                    light_matches['amplitudes'].append(light_hit['wvfm_max'])
                    light_matches['x'].append(clusters_event[clusters_chunk_mask][0]['x_mid'])
                    light_matches['y'].append(clusters_event[clusters_chunk_mask][0]['y_mid'])
                    light_matches['z'].append(clusters_event[clusters_chunk_mask][0]['z_drift_mid'])
                    light_matches['q'].append(clusters_event[clusters_chunk_mask][0]['q'])
                    light_matches['nhit'].append(clusters_event[clusters_chunk_mask][0]['nhit'])
                    light_matches['tile_x'].append(light_hit['tile_x'])
                    light_matches['tile_y'].append(light_hit['tile_y'])
                    light_matches['det_type'].append(light_hit['det_type'])
                    light_matches['t'].append(clusters_event[clusters_chunk_mask][0]['t_mid'])
                    light_matches['t0'].append(clusters_event[clusters_chunk_mask][0]['t0'])
                    light_matches['unix'].append(clusters_event[clusters_chunk_mask][0]['unix'])

                clusters_mask[clusters_event_mask] = clusters_chunk_mask
        clusters = clusters[clusters_mask]
    
    return clusters, light_matches, f90_values

def saveNPZ(filename, light_matches, files):
    ### save clusters/light data for charge light matches
    # Inputs: filename; filename for npz file
    #         light_matches; list of dictionaries with C+L data
    #         files; list of CRS files used
    amplitudes_all = []
    x_all = []
    y_all = []
    z_all = []
    q_all = []
    io_group_all = []
    nhit_all = []
    tile_x_all = []
    tile_y_all = []
    det_type_all = []
    t_all = []
    t0_all = []
    unix_all = []

    for light_match_list in light_matches:
        amplitudes_all += light_match_list['amplitudes']
        x_all += light_match_list['x']
        y_all += light_match_list['y']
        z_all += light_match_list['z']
        q_all += light_match_list['q']
        io_group_all += light_match_list['io_group']
        nhit_all += light_match_list['nhit']
        tile_x_all += light_match_list['tile_x']
        tile_y_all += light_match_list['tile_y']
        det_type_all += light_match_list['det_type']
        t_all += light_match_list['t']
        t0_all += light_match_list['t0']
        unix_all += light_match_list['unix']

    np.savez(filename, amplitudes=amplitudes_all, x=x_all, y=y_all, \
            z=z_all, q=q_all, io_group=io_group_all, nhit=nhit_all, tile_x=tile_x_all, \
            tile_y=tile_y_all, det_type=det_type_all, t=t_all, t0=t0_all, unix=unix_all, files=files)

def linear_fit(x, y, error, axes, make_plot=True):
    # Weighted least squares regression
    error[error == 0] = 1.15
    weights = 1 / (error ** 2)
    # Calculate slope (m) and intercept (b)
    sum_w = np.sum(weights)
    sum_wx = np.sum(weights * x)
    sum_wy = np.sum(weights * y)
    sum_wxx = np.sum(weights * x ** 2)
    sum_wxy = np.sum(weights * x * y)
    print(f'sum_w={sum_w}; sum_wx={sum_wx}; sum_wy={sum_wy}; sum_wxx={sum_wxx}; sum_wxy={sum_wxy}')
    m = (sum_wxy - (sum_wx * sum_wy) / sum_w) / (sum_wxx - (sum_wx ** 2) / sum_w)
    b = (sum_wy - m * sum_wx) / sum_w

    # Calculate uncertainties in slope (Delta m) and intercept (Delta b)
    delta_m = np.sqrt(1 / (sum_wxx - (sum_wx ** 2) / sum_w))
    delta_b = np.sqrt(sum_wxx / (sum_w * (sum_wxx - (sum_wx ** 2) / sum_w)))

    # Calculate chi-squared
    chi_squared = np.sum(((y - (m * x + b)) / error) ** 2)
    # Create plot
    #axes.errorbar(x, y, yerr=error, fmt='o', label='Data points with uncertainties', markersize=5)
    if make_plot:
        axes.plot(x, m * x + b) # label=f'Best-fit line: y = {m:.2f}x + {b:.2f}'
        #axes.fill_between(x, (m - delta_m) * x + (b - delta_b), (m + delta_m) * x + (b + delta_b), color='gray', alpha=0.5)
    return m, b, delta_m, delta_b, chi_squared

def poisson_interval(k, alpha=0.05): 
    """
    uses chisquared info to get the poisson interval. Uses scipy.stats 
    (imports in function). 
    """
    from scipy.stats import chi2
    a = alpha
    low, high = (chi2.ppf(a/2, 2*k) / 2, chi2.ppf(1-a/2, 2*k + 2) / 2)
    if k == 0: 
        low = 0.0
    return low, high

def matching_purity(clusters, total_time, q_bins=6, q_range=None, plot_vlines=True, plot_log_scale=False, plot_legend=True, figTitle=None, imageFileName=None, ylim=None): 
    fig, axes = plt.subplots(nrows=3, ncols=2, sharex=False, sharey=False, figsize=(10,11))
    q_io1 = clusters[clusters['io_group'] == 1]['q']*221*1e-3
    q_io2 = clusters[clusters['io_group'] == 2]['q']*221*1e-3
    z_drift_mid_io1 = clusters[clusters['io_group'] == 1]['z_drift_mid']
    z_drift_mid_io2 = clusters[clusters['io_group'] == 2]['z_drift_mid']
    
    plot_bins = q_bins
    if q_range is None:
        q_min_max = [0, 50]
    else:
        q_min_max = [q_range[0], q_range[1]]
    plot_binsize = (q_min_max[1] - q_min_max[0])/plot_bins
    interval = 0.683

    matching_purity_io1, matching_purity_io2 = [], []
    matching_purity_error_io1, matching_purity_error_io2 = [], []
    real_matches_io1, real_matches_io2 = [], []
    real_matches_error_io1, real_matches_error_io2 = [], []

    q_for_plot = []
    q_values = []
    x_mid_values, y_mid_values, z_drift_values = [], [], []

    Range_io2 = [-400, 600]
    Range_io1 = [-600, 400]
    nbins = 150
    
    max_bins_io1 = []
    max_bins_io2 = []
    # loop through charge bins and plot z_reco distribution + calculate matching purity
    for i in tqdm(range(plot_bins)):

        # start and end points to consider for this charge bin
        start = q_min_max[0] + i*plot_binsize
        end = q_min_max[0] + (i+1)*plot_binsize

        # get z points for this selection and particular io group
        mask_io1 = (q_io1 > start) & (q_io1 < end) #& (x_mid_io1 > -280) & (x_mid_io1 < -270)
        z_drift_sel_io1 = z_drift_mid_io1[mask_io1]
        mask_io2 = (q_io2 > start) & (q_io2 < end) #& (x_mid_io2 > -280) & (x_mid_io2 < -270)
        z_drift_sel_io2 = z_drift_mid_io2[mask_io2]

        ### make TPC 2 histogram
        #if i < 1000:
        #ax0 = axes[1].hist(z_drift_sel_io2, bins=nbins, range=(Range_io2[0], Range_io2[1]), label=f'{(start / (1/221) * 1e-3):.2f} < q < {(end / (1/221) * 1e-3):.2f} ke-', histtype='step')
        ax0 = axes[0][1].hist(z_drift_sel_io2, bins=nbins, range=(Range_io2[0], Range_io2[1]), label=f'{start:.2f} < q < {end:.2f} ke-', histtype='step')
        bincenters_io2, bincontents_io2 = ax0[1], ax0[0]
        max_bins_io2.append(np.max(bincontents_io2))
        TPC2_errorbars = np.zeros((2, len(bincontents_io2)))
        for j, C in enumerate(bincontents_io2):
            TPC2_errorbars[:, j] = np.abs(np.array(list(poisson_interval(C, alpha=1-interval))) - C)
        axes[0][1].errorbar(ax0[1][:-1] + 0.5*(Range_io2[1] - Range_io2[0])/nbins, ax0[0], yerr=TPC2_errorbars,color='k',fmt='o',markersize = 0.5, linewidth=0.5)
        axes[0][1].set_xlim(-240, 550)
        
        ### make TPC1 histogram
        #ax1 = axes[0].hist(z_drift_sel_io1, bins=nbins, range=(Range_io1[0], Range_io1[1]), label=f'{(start / (1/221) * 1e-3):.2f} < q < {(end / (1/221) * 1e-3):.2f} ke-', histtype='step')
        ax1 = axes[0][0].hist(z_drift_sel_io1, bins=nbins, range=(Range_io1[0], Range_io1[1]), label=f'{start:.2f} < q < {end:.2f} ke-', histtype='step')
        bincenters_io1, bincontents_io1 = ax1[1], ax1[0]
        max_bins_io1.append(np.max(bincontents_io1))
        TPC1_errorbars = np.zeros((2, len(bincontents_io1)))
        for j,C in enumerate(bincontents_io1):
            TPC1_errorbars[:, j] = np.abs(np.array(list(poisson_interval(C, alpha=1-interval))) - C)
        axes[0][0].errorbar(ax1[1][:-1] + 0.5*(Range_io1[1] - Range_io1[0])/nbins, ax1[0], yerr=TPC1_errorbars,color='k',fmt='o',markersize = 0.5, linewidth=0.5)
        axes[0][0].set_xlim(-550, 240)
        
        for k in range(0,2):
            if k == 0:
                LSB_min, LSB_max = -525, -325
                HSB_min, HSB_max = 0, 225
                SR_min, SR_max = -310.31, 0
                bincenters = bincenters_io1 
                bincontents = bincontents_io1
            elif k == 1:
                LSB_min, LSB_max = 325, 525
                HSB_min, HSB_max = -225, 0
                SR_min, SR_max = 0, 310.31
                bincenters = bincenters_io2
                bincontents = bincontents_io2
            # calculate errorbars in lower side band
            LSB_mask = ((bincenters[:-1] >= LSB_min) & (bincenters[:-1] <= LSB_max))
            LSB_errorbars = np.zeros((2, np.sum(LSB_mask)))
            for j,C in enumerate(bincontents[LSB_mask]):
                LSB_errorbars[:, j] = np.abs(np.array(list(poisson_interval(C, alpha=1-interval))) - C)
            LSB_sum = np.sum(bincontents[LSB_mask])

            # HSB mask
            HSB_mask = ((bincenters[:-1] >= HSB_min) & (bincenters[:-1] <= HSB_max))
            HSB_errorbars = np.zeros((2, np.sum(HSB_mask)))
            for j,C in enumerate(bincontents[HSB_mask]):
                HSB_errorbars[:, j] = np.abs(np.array(list(poisson_interval(C, alpha=1-interval))) - C)
            HSB_sum_errorbars = np.sqrt( np.sum( HSB_errorbars**2 , axis=1) )
            HSB_sum = np.sum(bincontents[HSB_mask])
            a = np.max(bincenters[:-1][HSB_mask]) - np.min(bincenters[:-1][HSB_mask]) # time range in HSB
            b = np.max(bincenters[:-1][LSB_mask]) - np.min(bincenters[:-1][LSB_mask]) # time range in LSB
            HSB_S = HSB_sum - (a/b)*LSB_sum # est signal counts in HSB
            sigma_N_HSB = np.sqrt(np.sum( HSB_errorbars**2 , axis=1)) # total error on HSB
            sigma_M = np.sqrt(np.sum( LSB_errorbars**2 , axis=1)) # total error on LSB
            sigma_B = (a/b)*sigma_M # total error on LSB scaled to SR
            sigma_S_HSB =  np.sqrt( sigma_N_HSB**2 + sigma_B**2 ) # error on est real matches in SR

            P_HSB = 1 - (a/b)*LSB_sum/HSB_sum
            P_errorbars_HSB = (a/b) * LSB_sum/HSB_sum * np.sqrt( ( sigma_M / LSB_sum )**2 + ( HSB_sum_errorbars / HSB_sum )**2 )
            print(f'Fraction of signal in HSB = {P_HSB}, error = {P_errorbars_HSB}')
            print(f'Total signal in HSB = {HSB_S}')
            print(f'Total sum in HSB = {HSB_sum}')
            
            ### calculate errorbars in signal region for TPC2
            SR_mask = (bincenters[:-1] >= SR_min) & (bincenters[:-1] <= SR_max)
            SR_sum = np.sum(bincontents[SR_mask])
            SR_errorbars = np.zeros((2, np.sum(SR_mask)))
            for j,C in enumerate(bincontents[SR_mask]):
                SR_errorbars[:, j] = np.abs(np.array(list(poisson_interval(C, alpha=1-interval))) - C)
            SR_sum_errorbars = np.sqrt( np.sum( SR_errorbars**2 , axis=1) )

            a = np.max(bincenters[:-1][SR_mask]) - np.min(bincenters[:-1][SR_mask]) # time range in SR
            b = np.max(bincenters[:-1][LSB_mask]) - np.min(bincenters[:-1][LSB_mask]) # time range in LSB
            S = SR_sum - (a/b)*LSB_sum # est signal counts in SR
            sigma_N = np.sqrt(np.sum( SR_errorbars**2 , axis=1)) # total error on SR
            sigma_M = np.sqrt(np.sum( LSB_errorbars**2 , axis=1)) # total error on LSB
            sigma_B = (a/b)*sigma_M # total error on LSB scaled to SR
            sigma_S =  np.sqrt( sigma_N**2 + sigma_B**2 ) # error on est real matches in SR

            P = 1 - (a/b)*LSB_sum/SR_sum
            P_errorbars = (a/b) * LSB_sum/SR_sum * np.sqrt( ( sigma_M / LSB_sum )**2 + ( SR_sum_errorbars / SR_sum )**2 )

            if k == 0:
                matching_purity_io1.append(P)
                matching_purity_error_io1.append(P_errorbars)
                real_matches_io1.append(S)
                real_matches_error_io1.append(sigma_S)
            elif k == 1:
                matching_purity_io2.append(P)
                matching_purity_error_io2.append(P_errorbars)
                real_matches_io2.append(S)
                real_matches_error_io2.append(sigma_S)
                
        q_for_plot.append((end+start)/2)
    if plot_vlines:
        axes[0][1].vlines(0, ymin=0, ymax=max(max_bins_io2)*1.5, color='y', label='cathode',linewidth=1)
        axes[0][1].vlines(304.31, ymin=0, ymax=max(max_bins_io2)*1.5, color='r', label='anode',linewidth=1)
        axes[0][0].vlines(0, ymin=0, ymax=max(max_bins_io1)*1.5, color='y', label='cathode',linewidth=1)
        axes[0][0].vlines(-304.31, ymin=0, ymax=max(max_bins_io1)*1.5, color='r', label='anode',linewidth=1)
    
    if ylim is not None:
        axes[0][0].set_ylim(ylim[0], ylim[1])
        axes[0][1].set_ylim(ylim[0], ylim[1])
    
    if plot_log_scale:
        axes[0][1].set_yscale('log')
        axes[0][0].set_yscale('log')
        
    if plot_legend:
        axes[0][1].legend(fontsize=4.5, loc='upper left')
        axes[0][0].legend(fontsize=4.5, loc='upper left')
    
    axes[0][0].set_xlabel(r'$x_{drift}$ [mm]')
    axes[0][1].set_xlabel(r'$x_{drift}$ [mm]') 
    axes[0][1].set_ylabel('Counts')
    axes[0][0].set_ylabel('Counts')
    
    axes[0][0].set_title('TPC1')
    axes[0][1].set_title('TPC2')
    #axes[0][0].text(0.85, 0.89, 'TPC1', transform=axes[0][0].transAxes,
    #     bbox=dict(facecolor='white', edgecolor='black', boxstyle='round,pad=0.5'))
    #axes[0][1].text(0.85, 0.89, 'TPC2', transform=axes[0][1].transAxes,
    #         bbox=dict(facecolor='white', edgecolor='black', boxstyle='round,pad=0.5'))

    axes[1][0].set_ylabel('Purity Fraction')
    axes[1][1].set_ylabel('Purity Fraction')
    axes[1][0].plot(q_for_plot, matching_purity_io1, 'bo', markersize=3,label='TPC1')
    if plot_bins > 1:
        xerr=np.ones_like(q_for_plot)*(q_for_plot[1] - q_for_plot[0])/2
    else:
        xerr=None
    axes[1][0].errorbar(q_for_plot, matching_purity_io1, xerr=xerr,yerr=np.array(matching_purity_error_io1).transpose(),color='k',fmt='o',markersize = 0.5, linewidth=1)
    #fig.suptitle('Purity Fraction of Real Charge-Light Matched Charge Clusters \n (module-1, 5 hrs of data, 2022_02_08)')
    axes[1][1].set_xlabel('Cluster Charge [ke-]')
    axes[1][0].set_xlabel('Cluster Charge [ke-]')
    #axes[1][1].plot(q_for_plot, matching_purity_io2, 'bo', markersize=3, label='TPC2')
    axes[1][1].errorbar(q_for_plot, matching_purity_io2, xerr=xerr,yerr=np.array(matching_purity_error_io2).transpose(),color='k',fmt='o',markersize = 0.5, linewidth=1)
    min_purity = min(min(matching_purity_io1), min(matching_purity_io2))
    max_purity = max(max(matching_purity_io1), max(matching_purity_io2))
    axes[1][1].set_ylim(min_purity-0.015, max_purity+0.015)
    axes[1][0].set_ylim(min_purity-0.015, max_purity+0.015)
    
    print(f'tpc 1 rates: {np.array(real_matches_io1)/total_time}')
    print(f'tpc 2 rates: {np.array(real_matches_io2)/total_time}')
    axes[2][0].errorbar(q_for_plot, np.array(real_matches_io1)/total_time, xerr=xerr,yerr=np.array(real_matches_error_io1).transpose()/total_time,color='k',fmt='o',markersize = 0.5, linewidth=1)
    #fig.suptitle('Purity Fraction of Real Charge-Light Matched Charge Clusters \n (module-1, 5 hrs of data, 2022_02_08)')
    axes[2][1].set_xlabel('Cluster Charge [ke-]')
    axes[2][0].set_xlabel('Cluster Charge [ke-]')
    axes[2][1].set_ylabel('Rate [Hz]')
    axes[2][0].set_ylabel('Rate [Hz]')
    #axes[2][1].plot(q_for_plot, real_matches_io2, 'bo', markersize=3, label='TPC2')
    axes[2][1].errorbar(q_for_plot, np.array(real_matches_io2)/total_time, xerr=xerr,yerr=np.array(real_matches_error_io2).transpose()/total_time,color='k',fmt='o',markersize = 0.5, linewidth=1)
    
    max_rate = max(max(np.array(real_matches_io2)/total_time), max(np.array(real_matches_io1)/total_time))
    max_rate = ceil(max_rate)+0.5
    axes[2][1].set_ylim(-0.5, max_rate)
    axes[2][0].set_ylim(-0.5, max_rate)
    fig.suptitle(figTitle)
    if imageFileName is not None:
        plt.savefig(imageFileName)
    plt.show()
    
def ACL_distribution(clusters_all, nbins, figTitle=None, weight_type=None):
    z_mask = (clusters_all['z_drift_mid'] > 0) & (clusters_all['z_drift_mid'] < 310)
    y_mask = (clusters_all['y_mid'] > 0) & (clusters_all['y_mid'] < 310)
    x_mask = clusters_all['x_mid'] > 0
    y_1, z_1, q_1 = clusters_all[z_mask & y_mask & x_mask]['y_mid'], clusters_all[z_mask & y_mask & x_mask]['z_drift_mid'], clusters_all[z_mask & y_mask & x_mask]['q']*221*1e-3

    z_mask = (clusters_all['z_drift_mid'] > 0) & (clusters_all['z_drift_mid'] < 310)
    y_mask = (clusters_all['y_mid'] > -620) & (clusters_all['y_mid'] < -310)
    x_mask = clusters_all['x_mid'] > 0
    y_2, z_2, q_2 = clusters_all[z_mask & y_mask & x_mask]['y_mid'], clusters_all[z_mask & y_mask & x_mask]['z_drift_mid'], clusters_all[z_mask & y_mask & x_mask]['q']*221*1e-3
    y_2 += 620

    z_mask = (clusters_all['z_drift_mid'] > 0) & (clusters_all['z_drift_mid'] < 310)
    y_mask = (clusters_all['y_mid'] > 0) & (clusters_all['y_mid'] < 310)
    x_mask = clusters_all['x_mid'] < 0
    y_3, z_3, q_3 = clusters_all[z_mask & y_mask & x_mask]['y_mid'], clusters_all[z_mask & y_mask & x_mask]['z_drift_mid'], clusters_all[z_mask & y_mask & x_mask]['q']*221*1e-3

    z_mask = (clusters_all['z_drift_mid'] > 0) & (clusters_all['z_drift_mid'] < 310)
    y_mask = (clusters_all['y_mid'] > -620) & (clusters_all['y_mid'] < -310)
    x_mask = clusters_all['x_mid'] < 0
    y_4, z_4, q_4 = clusters_all[z_mask & y_mask & x_mask]['y_mid'], clusters_all[z_mask & y_mask & x_mask]['z_drift_mid'], clusters_all[z_mask & y_mask & x_mask]['q']*221*1e-3
    y_4 += 620

    z_mask = (clusters_all['z_drift_mid'] < 0) & (clusters_all['z_drift_mid'] > -310)
    y_mask = (clusters_all['y_mid'] > 0) & (clusters_all['y_mid'] < 310)
    x_mask = clusters_all['x_mid'] > 0
    y_5, z_5, q_5 = clusters_all[z_mask & y_mask & x_mask]['y_mid'], clusters_all[z_mask & y_mask & x_mask]['z_drift_mid'], clusters_all[z_mask & y_mask & x_mask]['q']*221*1e-3
    z_5 *= -1

    z_mask = (clusters_all['z_drift_mid'] < 0) & (clusters_all['z_drift_mid'] > -310)
    y_mask = (clusters_all['y_mid'] > -620) & (clusters_all['y_mid'] < -310)
    x_mask = clusters_all['x_mid'] > 0
    y_6, z_6, q_6 = clusters_all[z_mask & y_mask & x_mask]['y_mid'], clusters_all[z_mask & y_mask & x_mask]['z_drift_mid'], clusters_all[z_mask & y_mask & x_mask]['q']*221*1e-3
    y_6 += 620
    z_6 *= -1

    z_mask = (clusters_all['z_drift_mid'] < 0) & (clusters_all['z_drift_mid'] > -310)
    y_mask = (clusters_all['y_mid'] > 0) & (clusters_all['y_mid'] < 310)
    x_mask = clusters_all['x_mid'] < 0
    y_7, z_7, q_7= clusters_all[z_mask & y_mask & x_mask]['y_mid'], clusters_all[z_mask & y_mask & x_mask]['z_drift_mid'], clusters_all[z_mask & y_mask & x_mask]['q']*221*1e-3
    z_7 *= -1

    z_mask = (clusters_all['z_drift_mid'] < 0) & (clusters_all['z_drift_mid'] > -310)
    y_mask = (clusters_all['y_mid'] > -620) & (clusters_all['y_mid'] < -310)
    x_mask = clusters_all['x_mid'] < 0
    y_8, z_8, q_8 = clusters_all[z_mask & y_mask & x_mask]['y_mid'], clusters_all[z_mask & y_mask & x_mask]['z_drift_mid'], clusters_all[z_mask & y_mask & x_mask]['q']*221*1e-3
    y_8 += 620
    z_8 *= -1

    y_all = np.concatenate((y_1, y_2, y_3, y_4, y_5, y_6, y_7, y_8))
    z_all = np.concatenate((z_1, z_2, z_3, z_4, z_5, z_6, z_7, z_8))
    q_all = np.concatenate((q_1, q_2, q_3, q_4, q_5, q_6, q_7, q_8))

    # Create a 2D histogram
    hist, xedges, yedges = np.histogram2d(y_all, z_all, bins=nbins, range=[[0, 310],[0, 310]])

    # Define the extent of the plot
    extent = [0, 310, 0, 310]

    if weight_type == 'q':
        norm = None
        fig, axes = plt.subplots(nrows=1, ncols=1, sharex=False, sharey=False, figsize=figsize)
        cmap = plt.cm.jet
        hist_data = stats.binned_statistic_2d(y_all, z_all, q_all, statistic='mean', bins=[x_bins,y_bins], range=[[0, 310], [0, 310]])
        im = axes.imshow(hist_data.statistic.T, cmap=cmap,norm=norm, origin='lower', extent=[0, 310, 0, 310])
        colorbar = plt.colorbar(im, ax=axes)
        axes.set_xlabel(r'$z_{drift}$ [mm]')
        axes.set_ylabel('y [mm]')
        #im.set_clim(vmin, vmax)
    else:
        # Plot the contour plot
        from matplotlib.colors import LogNorm
        #plt.contour(hist, extent=extent)
        plt.imshow(hist, extent=[0, 310, 0, 310], origin='lower', aspect='auto')
        plt.xlabel(r'$z_{drift}$ [mm]')
        plt.ylabel('y [mm]')
        plt.colorbar()
    if figTitle is not None:
        plt.savefig(figTitle)
        
def LCM_distribution(clusters_all, nbins, figTitle=None):
    z_mask = (clusters_all['z_drift_mid'] > 0) & (clusters_all['z_drift_mid'] < 310)
    y_mask = (clusters_all['y_mid'] > 0+310) & (clusters_all['y_mid'] < 310+310)
    x_mask = clusters_all['x_mid'] > 0
    y_1, z_1 = clusters_all[z_mask & y_mask & x_mask]['y_mid'], clusters_all[z_mask & y_mask & x_mask]['z_drift_mid']
    y_1 -= 310

    z_mask = (clusters_all['z_drift_mid'] > 0) & (clusters_all['z_drift_mid'] < 310)
    y_mask = (clusters_all['y_mid'] > -620+310) & (clusters_all['y_mid'] < -310+310)
    x_mask = clusters_all['x_mid'] > 0
    y_2, z_2 = clusters_all[z_mask & y_mask & x_mask]['y_mid'], clusters_all[z_mask & y_mask & x_mask]['z_drift_mid']
    y_2 -= -310

    z_mask = (clusters_all['z_drift_mid'] > 0) & (clusters_all['z_drift_mid'] < 310)
    y_mask = (clusters_all['y_mid'] > 0+310) & (clusters_all['y_mid'] < 310+310)
    x_mask = clusters_all['x_mid'] < 0
    y_3, z_3 = clusters_all[z_mask & y_mask & x_mask]['y_mid'], clusters_all[z_mask & y_mask & x_mask]['z_drift_mid']
    y_3 -= 310

    z_mask = (clusters_all['z_drift_mid'] > 0) & (clusters_all['z_drift_mid'] < 310)
    y_mask = (clusters_all['y_mid'] > -620+310) & (clusters_all['y_mid'] < -310+310)
    x_mask = clusters_all['x_mid'] < 0
    y_4, z_4 = clusters_all[z_mask & y_mask & x_mask]['y_mid'], clusters_all[z_mask & y_mask & x_mask]['z_drift_mid']
    y_4 -= -310

    z_mask = (clusters_all['z_drift_mid'] < 0) & (clusters_all['z_drift_mid'] > -310)
    y_mask = (clusters_all['y_mid'] > 0+310) & (clusters_all['y_mid'] < 310+310)
    x_mask = clusters_all['x_mid'] > 0
    y_5, z_5 = clusters_all[z_mask & y_mask & x_mask]['y_mid'], clusters_all[z_mask & y_mask & x_mask]['z_drift_mid']
    y_5 -= 310
    z_5 *= -1

    z_mask = (clusters_all['z_drift_mid'] < 0) & (clusters_all['z_drift_mid'] > -310)
    y_mask = (clusters_all['y_mid'] > -620+310) & (clusters_all['y_mid'] < -310+310)
    x_mask = clusters_all['x_mid'] > 0
    y_6, z_6 = clusters_all[z_mask & y_mask & x_mask]['y_mid'], clusters_all[z_mask & y_mask & x_mask]['z_drift_mid']
    y_6 -= -310
    z_6 *= -1

    z_mask = (clusters_all['z_drift_mid'] < 0) & (clusters_all['z_drift_mid'] > -310)
    y_mask = (clusters_all['y_mid'] > 0+310) & (clusters_all['y_mid'] < 310+310)
    x_mask = clusters_all['x_mid'] < 0
    y_7, z_7 = clusters_all[z_mask & y_mask & x_mask]['y_mid'], clusters_all[z_mask & y_mask & x_mask]['z_drift_mid']
    y_7 -= 310
    z_7 *= -1

    z_mask = (clusters_all['z_drift_mid'] < 0) & (clusters_all['z_drift_mid'] > -310)
    y_mask = (clusters_all['y_mid'] > -620+310) & (clusters_all['y_mid'] < -310+310)
    x_mask = clusters_all['x_mid'] < 0
    y_8, z_8 = clusters_all[z_mask & y_mask & x_mask]['y_mid'], clusters_all[z_mask & y_mask & x_mask]['z_drift_mid']
    y_8 -= -310
    z_8 *= -1

    y_all = np.concatenate((y_1, y_2, y_3, y_4, y_5, y_6, y_7, y_8))
    z_all = np.concatenate((z_1, z_2, z_3, z_4, z_5, z_6, z_7, z_8))

    # Create a 2D histogram
    hist, xedges, yedges = np.histogram2d(y_all, z_all, bins=nbins, range=[[0, 310],[0, 310]])

    # Define the extent of the plot
    extent = [0, 310, 0, 310]

    # Plot the contour plot
    from matplotlib.colors import LogNorm
    #plt.contour(hist, extent=extent)
    plt.imshow(hist, extent=[0, 310, 0, 310], origin='lower', aspect='auto')
    plt.xlabel(r'$z_{drift}$ [mm]')
    plt.ylabel('y [mm]')
    plt.colorbar()
    if figTitle is not None:
        plt.savefig(figTitle)
def get_charge_MC(nFiles_dict, folders_MC, filename_ending_MC, nbins, do_calibration, recomb_filename,disable_alphas=False, disable_gammas=False, disable_betas=False):
    # Isotope ratios
    isotopes_ratios_betas_gammas = { 
        '85Kr': 224.76, # beta/gamma ratio
        '60Co': 0.5,
        '40K': 8.46
    }
    
    isotopes_ratios_betas_alphas_gammas_alphas = {
        '232Th': [0.649, 0.45], # betas/alphas , gammas/alphas ratios
        '238U': [0.751, 0.999]
    }
    
    # Initialize dictionaries
    charge_dict = {}
    hist_data_dict = {}
    
    # Loop over isotopes
    for iso_decay, nFiles in nFiles_dict.items():
        iso, decay = iso_decay.split('_')
        folder = folders_MC[iso_decay]
        ending = filename_ending_MC[iso_decay]
        # Loop over files
        for i in range(1, nFiles+1):
            f = h5py.File(folder + f'larndsim_{iso}_{decay}_10000_{i}_{ending}.h5', 'r')
            charge_temp = f['clusters']['q']
            if i == 1:
                charge_dict[iso_decay] = charge_temp
            else:
                charge_dict[iso_decay] = np.concatenate((charge_dict[iso_decay], charge_temp))
        
        # Call function to get histogram data
        bin_centers, bin_contents, bin_error = \
            get_hist_data(charge_dict[iso_decay], bins=nbins, data_type='MC', \
            calibrate=do_calibration, recomb_filename=recomb_filename)
        
        hist_data_dict[iso_decay] = {
            'bin_centers': bin_centers,
            'bin_contents': bin_contents,
            'bin_error': bin_error
        }
    
    # Combine y_norm and y_norm_std for isotopes that have betas and gammas
    for iso in isotopes_ratios_betas_gammas.keys():
        R = isotopes_ratios_betas_gammas[iso]
        x_1 = R * (np.sum(hist_data_dict[iso+'_gammas']['bin_contents']) / np.sum(hist_data_dict[iso+'_betas']['bin_contents']))
        x_2 = 1
        
        if disable_gammas:
            x_2 = 0
        if disable_betas:
            x_1 = 0
        hist_data_dict[iso] = {
            'bin_centers': hist_data_dict[iso+'_betas']['bin_centers'],
            'bin_contents': hist_data_dict[iso+'_betas']['bin_contents']*x_1 + hist_data_dict[iso+'_gammas']['bin_contents']*x_2,
            'bin_error': np.sqrt((hist_data_dict[iso+'_betas']['bin_error']*x_1)**2 + (hist_data_dict[iso+'_gammas']['bin_error']*x_2)**2)
        }
    for iso in isotopes_ratios_betas_alphas_gammas_alphas.keys():
        R = isotopes_ratios_betas_alphas_gammas_alphas[iso]
        x_1 = R[0] * (np.sum(hist_data_dict[iso+'_alphas']['bin_contents']) / np.sum(hist_data_dict[iso+'_betas']['bin_contents']))
        x_2 = R[1] * (np.sum(hist_data_dict[iso+'_alphas']['bin_contents']) / np.sum(hist_data_dict[iso+'_gammas']['bin_contents']))
        x_3 = 1
        if disable_betas:
            x_1 = 0
        if disable_gammas:
            x_2 = 0
        if disable_alphas:
            x_3 = 0
        hist_data_dict[iso] = {
            'bin_centers': hist_data_dict[iso+'_betas']['bin_centers'],
            'bin_contents': hist_data_dict[iso+'_betas']['bin_contents']*x_1 + hist_data_dict[iso+'_gammas']['bin_contents']*x_2 + \
                (hist_data_dict[iso+'_alphas']['bin_contents']*x_3),
            'bin_error': np.sqrt((hist_data_dict[iso+'_betas']['bin_error']*x_1)**2 + (hist_data_dict[iso+'_gammas']['bin_error']*x_2)**2 \
                                + (hist_data_dict[iso+'_alphas']['bin_error']*x_3)**2)
        }
    return charge_dict, hist_data_dict

def plot_isotopes(hist_data_dict, axes, colors, norm=None, linewidth=2, do_not_plot_list=None):    
    # Loop over isotopes
    for iso_decay, color in colors.items():
        # Get histogram data
        bin_centers = hist_data_dict[iso_decay]['bin_centers']
        bin_contents = hist_data_dict[iso_decay]['bin_contents']
        bin_error = hist_data_dict[iso_decay]['bin_error']
        
        if len(iso_decay.split('_')) > 1:
            label = iso_decay.split('_')[0]
        else:
            label = iso_decay
        if label not in do_not_plot_list:
            # Call function to plot histogram
            plot_hist(bin_centers, bin_contents, bin_error, axes, color, linewidth, label, norm=norm)
            
def plot_3d_density(x, y, z):
    
    import plotly.graph_objects as go
    import numpy as np
    from scipy.stats import gaussian_kde
    # Calculate the point density
    data = np.vstack([x, y, z])
    kde = gaussian_kde(data)
    density = kde(data)
    
    fig = go.Figure(data=go.Scatter3d(
        x=x,
        y=y,
        z=z,
        mode='markers',
        marker=dict(
            size=2.5,
            color=density,
            colorscale='Blues',
            opacity=0.6
        )
    ))

    # Adjusting the aspect ratio and camera position for vertical y-axis
    fig.update_layout(
        scene=dict(
            xaxis=dict(range=[-310, 310]),
            yaxis=dict(range=[-620, 620]),
            zaxis=dict(range=[-310, 310]),
            aspectmode='manual',
            aspectratio=dict(x=1, y=4, z=1),
            camera=dict(
                up=dict(x=0, y=1, z=0),  # this makes the z-axis point upward
                center=dict(x=0, y=0, z=0),
                eye=dict(x=1.5, y=1.5, z=0.5)
            )
        )
    )
    
    fig.show()
    

