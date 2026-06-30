function bach_run_miditoolbox_features()
%BACH_RUN_MIDITOOLBOX_FEATURES Extract MIDI Toolbox features for beta-sync Bach.
%
% Outputs:
%   analysis/matlab_toolbox_features/miditoolbox_whole_piece_features.csv
%   analysis/matlab_toolbox_features/miditoolbox_binned_features.csv

bach_root = fileparts(fileparts(mfilename('fullpath')));
manifest_path = fullfile(bach_root, 'alignment', 'beta_midi_sync_draft', 'bach_beta_midi_sync_manifest.csv');
out_dir = fullfile(bach_root, 'analysis', 'matlab_toolbox_features');
midi_toolbox_root = fullfile(bach_root, 'miditoolbox-1.1', 'miditoolbox');

if ~exist(out_dir, 'dir')
    mkdir(out_dir);
end
addpath(genpath(midi_toolbox_root));

manifest = readtable(manifest_path, 'TextType', 'string', 'VariableNamingRule', 'preserve', 'Delimiter', ',');
window_s = 1.0;
hop_s = 0.25;

whole_rows = {};
bin_rows = {};

for ii = 1:height(manifest)
    stim_name = manifest.stim_name(ii);
    wtc_code = manifest.wtc_code(ii);
    midi_path = manifest.beta_midi_path(ii);
    fprintf('MIDI Toolbox track %d/%d: %s\n', ii, height(manifest), stim_name);
    if ~isfile(midi_path)
        warning('Missing MIDI: %s', midi_path);
        continue;
    end
    try
        nmat = readmidi(char(midi_path));
    catch ME
        warning('readmidi failed for %s: %s', midi_path, ME.message);
        continue;
    end
    if isempty(nmat)
        continue;
    end

    ons = onset(nmat, 'sec');
    durs = dur(nmat, 'sec');
    pit = pitch(nmat);
    ons = ons(:);
    durs = durs(:);
    pit = pit(:);
    first_onset = min(ons);
    ons_aligned = ons - first_onset;
    duration_s = max(ons_aligned + durs);
    iois = diff(sort(ons_aligned));

    whole_rows(end+1,:) = { ...
        char(stim_name), char(wtc_code), char(midi_path), ...
        size(nmat,1), duration_s, safe_notedensity(nmat), ...
        mean(pit, 'omitnan'), std(pit, 'omitnan'), min(pit), max(pit), ...
        mean(durs, 'omitnan'), std(durs, 'omitnan'), ...
        mean(iois, 'omitnan'), std(iois, 'omitnan'), safe_cv(iois), ...
        numel(unique(round(ons_aligned, 6))) ...
    }; %#ok<AGROW>

    starts = 0:hop_s:max(0, duration_s - window_s);
    if isempty(starts)
        starts = 0;
    end
    for ss = 1:numel(starts)
        w0 = starts(ss);
        w1 = min(duration_s, w0 + window_s);
        in_window = ons_aligned >= w0 & ons_aligned < w1;
        active = ons_aligned < w1 & (ons_aligned + durs) > w0;
        sub_ons = sort(ons_aligned(in_window));
        sub_ioi = diff(sub_ons);
        sub_pitch = pit(in_window);
        sub_dur = durs(in_window);
        bin_rows(end+1,:) = { ...
            char(stim_name), char(wtc_code), w0, w1, (w0+w1)/2, char(midi_path), ...
            sum(in_window), sum(in_window) / max(eps, (w1-w0)), ...
            mean(sub_pitch, 'omitnan'), std(sub_pitch, 'omitnan'), ...
            mean(sub_dur, 'omitnan'), std(sub_dur, 'omitnan'), ...
            mean(sub_ioi, 'omitnan'), std(sub_ioi, 'omitnan'), safe_cv(sub_ioi), ...
            sum(active), sum(active) / max(1, sum(in_window)) ...
        }; %#ok<AGROW>
    end
end

whole_names = { ...
    'stim_name','wtc_code','midi_path','n_notes','duration_s','notedensity_per_s', ...
    'pitch_mean','pitch_std','pitch_min','pitch_max', ...
    'duration_mean_s','duration_std_s','ioi_mean_s','ioi_std_s','ioi_cv', ...
    'unique_onset_count' ...
};
if ~isempty(whole_rows)
    whole_tbl = cell2table(whole_rows, 'VariableNames', whole_names);
else
    whole_tbl = cell2table(cell(0, numel(whole_names)), 'VariableNames', whole_names);
end
writetable(whole_tbl, fullfile(out_dir, 'miditoolbox_whole_piece_features.csv'));

bin_names = { ...
    'stim_name','wtc_code','window_start_s','window_end_s','window_center_s','midi_path', ...
    'mtb_n_note_onsets','mtb_note_onset_density_per_s', ...
    'mtb_pitch_mean','mtb_pitch_std','mtb_duration_mean_s','mtb_duration_std_s', ...
    'mtb_ioi_mean_s','mtb_ioi_std_s','mtb_ioi_cv', ...
    'mtb_active_note_count','mtb_approx_polyphony' ...
};
if ~isempty(bin_rows)
    bin_tbl = cell2table(bin_rows, 'VariableNames', bin_names);
else
    bin_tbl = cell2table(cell(0, numel(bin_names)), 'VariableNames', bin_names);
end
writetable(bin_tbl, fullfile(out_dir, 'miditoolbox_binned_features.csv'));
fprintf('Wrote MIDI Toolbox features to %s\n', out_dir);
end

function n = safe_notedensity(nmat)
try
    n = notedensity(nmat, 'sec');
catch
    n = nan;
end
end

function cv = safe_cv(x)
x = x(:);
x = x(isfinite(x));
if numel(x) > 1 && mean(x) > 0
    cv = std(x) / mean(x);
else
    cv = nan;
end
end
