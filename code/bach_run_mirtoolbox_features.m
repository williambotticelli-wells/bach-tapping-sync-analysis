function bach_run_mirtoolbox_features()
%BACH_RUN_MIRTOOLBOX_FEATURES Extract MIRToolbox features for beta-sync Bach.
%
% Outputs:
%   analysis/matlab_toolbox_features/mirtoolbox_whole_piece_features.csv
%   analysis/matlab_toolbox_features/mirtoolbox_binned_features.csv

bach_root = fileparts(fileparts(mfilename('fullpath')));
manifest_path = fullfile(bach_root, 'alignment', 'beta_midi_sync_draft', 'bach_beta_midi_sync_manifest.csv');
out_dir = fullfile(bach_root, 'analysis', 'matlab_toolbox_features');
mir_root = fullfile(bach_root, 'MIRtoolbox1.8.2');
zohar_scripts = fullfile(bach_root, 'for_zohar_scripts');

if ~exist(out_dir, 'dir')
    mkdir(out_dir);
end
addpath(genpath(mir_root));
addpath(genpath(zohar_scripts));

manifest = readtable(manifest_path, 'TextType', 'string', 'VariableNamingRule', 'preserve', 'Delimiter', ',');
window_s = 1.0;
hop_s = 0.25;

bin_rows = {};
status_rows = {};
whole_rows = {};
whole_names = {};

for ii = 1:height(manifest)
    stim_name = manifest.stim_name(ii);
    wtc_code = manifest.wtc_code(ii);
    wav_path = manifest.deployed_t0_wav(ii);
    wav_path_char = char(wav_path);
    fprintf('MIRToolbox track %d/%d: %s\n', ii, height(manifest), stim_name);
    if ~isfile(wav_path_char)
        warning('Missing WAV: %s', wav_path_char);
        continue;
    end
    [y, fs] = audioread(wav_path_char);
    if size(y,2) > 1
        ymono = mean(y, 2);
    else
        ymono = y;
    end
    ymono = ymono(:);
    duration_s = numel(ymono) / fs;

    [whole_row, whole_names_candidate, status_row] = local_whole_piece_features(stim_name, wtc_code, wav_path_char, duration_s);
    status_rows(end+1,:) = status_row; %#ok<AGROW>
    if ~isempty(whole_row)
        if isempty(whole_names)
            whole_names = whole_names_candidate;
        end
        whole_rows(end+1,:) = whole_row; %#ok<AGROW>
    end

    rms_vals = local_framed_feature(wav_path_char, 'mirrms', window_s, hop_s);
    low_vals = local_framed_feature(wav_path_char, 'mirlowenergy', window_s, hop_s);
    bright_vals = local_framed_feature(wav_path_char, 'mirbrightness', window_s, hop_s);
    rough_vals = local_framed_feature(wav_path_char, 'mirroughness', window_s, hop_s);
    centroid_vals = local_framed_feature(wav_path_char, 'mircentroid', window_s, hop_s);
    n_bins = max([numel(rms_vals), numel(low_vals), numel(bright_vals), numel(rough_vals), numel(centroid_vals)]);
    for ss = 1:n_bins
        w0 = (ss - 1) * hop_s;
        w1 = min(duration_s, w0 + window_s);
        bin_rows(end+1,:) = { ...
            char(stim_name), char(wtc_code), w0, w1, (w0+w1)/2, wav_path_char, ...
            local_index_or_nan(rms_vals, ss), local_index_or_nan(low_vals, ss), ...
            local_index_or_nan(bright_vals, ss), local_index_or_nan(rough_vals, ss), ...
            local_index_or_nan(centroid_vals, ss) ...
        }; %#ok<AGROW>
    end
end

status_var_names = {'stim_name','wtc_code','source_audio_path','duration_s','whole_piece_status','whole_piece_note'};
status_tbl = cell2table(status_rows, 'VariableNames', status_var_names);
writetable(status_tbl, fullfile(out_dir, 'mirtoolbox_whole_piece_status.csv'));

if ~isempty(whole_rows)
    whole_var_names = [{'stim_name','wtc_code','source_audio_path','duration_s'}, matlab.lang.makeUniqueStrings(matlab.lang.makeValidName(whole_names))];
    whole_tbl = cell2table(whole_rows, 'VariableNames', whole_var_names);
    writetable(whole_tbl, fullfile(out_dir, 'mirtoolbox_whole_piece_features.csv'));
end

bin_var_names = { ...
    'stim_name','wtc_code','window_start_s','window_end_s','window_center_s','source_audio_path', ...
    'mir_rms','mir_lowenergy','mir_brightness','mir_roughness','mir_centroid' ...
};
if ~isempty(bin_rows)
    bin_tbl = cell2table(bin_rows, 'VariableNames', bin_var_names);
else
    bin_tbl = cell2table(cell(0, numel(bin_var_names)), 'VariableNames', bin_var_names);
end
writetable(bin_tbl, fullfile(out_dir, 'mirtoolbox_binned_features.csv'));
fprintf('Wrote MIRToolbox features to %s\n', out_dir);
end

function [whole_row, whole_names, status_row] = local_whole_piece_features(stim_name, wtc_code, wav_path, duration_s)
whole_row = {};
whole_names = {};
if exist('pdist', 'file') ~= 2
    status_row = {char(stim_name), char(wtc_code), char(wav_path), duration_s, ...
        'skipped_missing_statistics_toolbox', ...
        'Nori Compute_audio_features/mirfeatures requires pdist for some spectral features.'};
    return;
end
try
    [y, fs] = audioread(wav_path);
    [feature_vals, feature_names, feature_cnt] = Compute_audio_features(y, fs);
    whole_names = feature_names(1:feature_cnt);
    feature_cells = num2cell(feature_vals(1:feature_cnt));
    whole_row = [{char(stim_name), char(wtc_code), char(wav_path), duration_s}, feature_cells];
    status_row = {char(stim_name), char(wtc_code), char(wav_path), duration_s, ...
        'exported', ...
        sprintf('Exported %d Nori/Compute_audio_features whole-piece MIR features.', feature_cnt)};
catch ME
    status_row = {char(stim_name), char(wtc_code), char(wav_path), duration_s, ...
        'failed', ME.message};
end
end

function vals = local_framed_feature(wav_path, fn_name, window_s, hop_s)
vals = [];
try
    fn = str2func(fn_name);
    obj = fn(wav_path, 'Frame', window_s, 's', hop_s, 's');
    raw = mirgetdata(obj);
    if iscell(raw)
        raw = raw{1};
    end
    vals = squeeze(raw);
    vals = vals(:)';
catch ME
    warning('Framed %s failed for %s: %s', fn_name, wav_path, ME.message);
end
end

function val = local_index_or_nan(vals, idx)
val = nan;
if idx <= numel(vals)
    val = vals(idx);
end
end
