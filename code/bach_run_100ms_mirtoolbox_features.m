function bach_run_100ms_mirtoolbox_features()
%BACH_RUN_100MS_MIRTOOLBOX_FEATURES Extract short-window MIRToolbox features.
%
% Outputs:
%   analysis/matlab_toolbox_features/mirtoolbox_100ms_features.csv
%
% This complements the existing 1 s / 250 ms-hop MIRToolbox export with a
% 100 ms grid that can be joined to the 100 ms MIDI/tapping vectors. Keep the
% feature set conservative: energy and spectral descriptors are reasonable at
% this timescale; rhythm, tempo, and key descriptors are intentionally excluded.

bach_root = fileparts(fileparts(mfilename('fullpath')));
manifest_path = fullfile(bach_root, 'alignment', 'beta_midi_sync_draft', 'bach_beta_midi_sync_manifest.csv');
out_dir = fullfile(bach_root, 'analysis', 'matlab_toolbox_features');
mir_root = fullfile(bach_root, 'MIRtoolbox1.8.2');

if ~exist(out_dir, 'dir')
    mkdir(out_dir);
end
addpath(genpath(mir_root));

manifest = readtable(manifest_path, 'TextType', 'string', 'VariableNamingRule', 'preserve', 'Delimiter', ',');
window_s = 0.1;
hop_s = 0.1;
rows = {};

for ii = 1:height(manifest)
    stim_name = manifest.stim_name(ii);
    wtc_code = manifest.wtc_code(ii);
    wav_path = manifest.deployed_t0_wav(ii);
    wav_path_char = char(wav_path);
    fprintf('100 ms MIRToolbox track %d/%d: %s\n', ii, height(manifest), stim_name);
    if ~isfile(wav_path_char)
        warning('Missing WAV: %s', wav_path_char);
        continue;
    end

    info = audioinfo(wav_path_char);
    duration_s = info.Duration;
    rms_vals = local_framed_feature(wav_path_char, 'mirrms', window_s, hop_s);
    bright_vals = local_framed_feature(wav_path_char, 'mirbrightness', window_s, hop_s);
    rough_vals = local_framed_feature(wav_path_char, 'mirroughness', window_s, hop_s);
    centroid_vals = local_framed_feature(wav_path_char, 'mircentroid', window_s, hop_s);
    n_bins = max([ceil(duration_s / hop_s), numel(rms_vals), numel(bright_vals), numel(rough_vals), numel(centroid_vals)]);

    for ss = 1:n_bins
        w0 = (ss - 1) * hop_s;
        w1 = min(duration_s, w0 + window_s);
        if w0 >= duration_s
            continue;
        end
        rows(end+1,:) = { ...
            char(stim_name), char(wtc_code), ss - 1, w0, w1, (w0+w1)/2, w1-w0, wav_path_char, ...
            local_index_or_nan(rms_vals, ss), local_index_or_nan(bright_vals, ss), local_index_or_nan(rough_vals, ss), ...
            local_index_or_nan(centroid_vals, ss) ...
        }; %#ok<AGROW>
    end
end

var_names = { ...
    'stim_name','wtc_code','bin_index','bin_start_s','bin_end_s','bin_center_s','bin_width_s','source_audio_path', ...
    'mir100_rms','mir100_brightness','mir100_roughness','mir100_centroid' ...
};
if ~isempty(rows)
    out = cell2table(rows, 'VariableNames', var_names);
else
    out = cell2table(cell(0, numel(var_names)), 'VariableNames', var_names);
end
writetable(out, fullfile(out_dir, 'mirtoolbox_100ms_features.csv'));
fprintf('Wrote 100 ms MIRToolbox features to %s\n', out_dir);
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
