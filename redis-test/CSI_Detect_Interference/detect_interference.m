clc
clear
close all
%%
no_inter = load('ch_13_no_inter_csi.mat').data;
wi_inter = load('ch_13_wi_inter_csi.mat').data;

[no_n_pkt, no_inter_idx] = calculate_num_packets(no_inter);
[wi_n_pkt, wi_inter_idx] = calculate_num_packets(wi_inter);

n_fc = 52;

% figure()
% for idx = no_inter_idx
%     plot(abs(no_inter(idx, :)), 'b-')
%     hold on
% end
% for idx = wi_inter_idx
%     plot(abs(wi_inter(idx, :)), 'r-')
%     hold on
% end
% grid on
% xlim([1, n_fc])

win_size = 3;
no_inter_var = sliding_window_var(no_inter, win_size);
wi_inter_var = sliding_window_var(wi_inter, win_size);

no_inter_decision = zeros(1, no_n_pkt);
wi_inter_decision = zeros(1, wi_n_pkt);

no_inter_median = median(no_inter_var, 2);
wi_inter_median = median(wi_inter_var, 2);
no_inter_max = max(no_inter_var, [], 2);
wi_inter_max = max(wi_inter_var, [], 2);


%{
    Threshold, the lower the more sensitive to interference
    th:     Ori (I/N)           |   Consec (I/N)
    3.5:    85/314 -> 20/379    |   244/19 -> 226/37
    3.75:   77/322 -> 16/383    |   237/26 -> 213/50
    4.0:    67/332 -> 13/386    |   232/31 -> 203/60
    4.25:   61/338 -> 11/388    |   221/42 -> 181/82
    4.5:    55/344 -> 10/389    |   213/50 -> 166/97
%}
median_max_threshold = 3.5;

figure()
subplot(2, 1, 1)
no_i = 0;
wi_i = 0;
for i = 1:length(no_inter_idx)
    idx = no_inter_idx(i);
    median_v = no_inter_median(idx);
    max_v = no_inter_max(idx);
    if max_v/median_v > median_max_threshold
        plot(no_inter_var(idx, :), 'r-')
        wi_i = wi_i + 1;
        no_inter_decision(i) = 1;
    else
        plot(no_inter_var(idx, :), 'b-')
        no_i = no_i + 1;
    end
    hold on
end
grid on
ylim([0, 0.01])
xlim([1, n_fc-win_size])
title(strcat('Not interfered:', num2str(no_i), '. Interfered: ', num2str(wi_i)))

subplot(2, 1, 2)
no_i = 0;
wi_i = 0;
for i = 1:length(wi_inter_idx)
    idx = wi_inter_idx(i);
    median_v = wi_inter_median(idx);
    max_v = wi_inter_max(idx);
    if max_v/median_v > median_max_threshold
        plot(wi_inter_var(idx, :), 'r-')
        wi_i = wi_i + 1;
        wi_inter_decision(i) = 1;
    else
        plot(wi_inter_var(idx, :), 'b-')
        no_i = no_i + 1;
    end
    hold on
end
grid on
ylim([0, 0.01])
xlim([1, n_fc-win_size])
title(strcat('Not interfered:', num2str(no_i), '. Interfered: ', num2str(wi_i)))


%% Check if conseccutive
no_inter_decision_consecutive = [no_inter_decision(1), no_inter_decision(1:end-1).*no_inter_decision(2:end)];
wi_inter_decision_consecutive = [wi_inter_decision(1), wi_inter_decision(1:end-1).*wi_inter_decision(2:end)];

figure()
subplot(2, 2, 1)
for i = 1:length(no_inter_decision)
    d = no_inter_decision(i);
    pattern = 'b.';
    if d == 1
        pattern = 'r.';
    end
    plot(i, d, pattern)
    hold on

    c_pattern = 'bx';
    d = no_inter_decision_consecutive(i);
    if no_inter_decision_consecutive(i) == 1
        c_pattern = 'ro';
    end
    plot(i, d, c_pattern)
    hold on
end
grid on
ylim([-0.1, 1.1])
str_1 = strcat(['Original: Detect interfered: ', num2str(sum(no_inter_decision)), ...
        '. Non-interfered: ', num2str(length(no_inter_decision) - sum(no_inter_decision)), '.']);
str_2 = strcat(['Consecutive: Detect interfered: ', num2str(sum(no_inter_decision_consecutive)), ...
        '. Non-interfered: ', num2str(length(no_inter_decision) - sum(no_inter_decision_consecutive)), '.']);
title({str_1, str_2})

subplot(2, 2, 2)
for i = 1:length(wi_inter_decision)
    d = wi_inter_decision(i);
    pattern = 'b.';
    if d == 1
        pattern = 'r.';
    end
    plot(i, d, pattern)
    hold on

    c_pattern = 'bx';
    d = wi_inter_decision_consecutive(i);
    if wi_inter_decision_consecutive(i) == 1
        c_pattern = 'ro';
    end
    plot(i, d, c_pattern)
end
grid on
ylim([-0.1, 1.1])
str_1 = strcat(['Original: Detect interfered: ', num2str(sum(wi_inter_decision)), ...
        '. Non-interfered: ', num2str(length(wi_inter_decision) - sum(wi_inter_decision)), '.']);
str_2 = strcat(['Consecutive: Detect interfered: ', num2str(sum(wi_inter_decision_consecutive)), ...
        '. Non-interfered: ', num2str(length(wi_inter_decision) - sum(wi_inter_decision_consecutive)), '.']);
title({str_1, str_2})

subplot(2, 2, 3)
for i = 1:length(no_inter_idx)
    pattern = 'b-';
    if no_inter_decision_consecutive(i) == 1
        pattern = 'r-';
    end
    plot(abs(no_inter(i, :)), pattern)
    hold on
end
grid on

subplot(2, 2, 4)
for i = 1:length(wi_inter_idx)
    pattern = 'b-';
    if wi_inter_decision_consecutive(i) == 1
        pattern = 'r-';
    end
    plot(abs(wi_inter(i, :)), pattern)
    hold on
end
grid on


%%
no_inter_t = load('ch_13_no_inter_timestamp.mat').data;
wi_inter_t = load('ch_13_wi_inter_timestamp.mat').data;

no_inter_non_zero_1st = find(no_inter_t, 1, 'first');
wi_inter_non_zero_1st = find(wi_inter_t, 1, 'first');

no_inter_cumm_t = zeros(1, length(no_inter_t));
wi_inter_cumm_t = zeros(1, length(wi_inter_t));
for i = 1:length(no_inter_t)
    if i < no_inter_non_zero_1st
        no_inter_cumm_t(i) = no_inter_t(no_inter_non_zero_1st);
    elseif no_inter_t(i) == 0
        no_inter_cumm_t(i) = no_inter_cumm_t(i-1);
    else
        no_inter_cumm_t(i) = no_inter_t(i);
    end

    if i < wi_inter_non_zero_1st
        wi_inter_cumm_t(i) = wi_inter_t(wi_inter_non_zero_1st);
    elseif wi_inter_t(i) == 0
        wi_inter_cumm_t(i) = wi_inter_cumm_t(i-1);
    else
        wi_inter_cumm_t(i) = wi_inter_t(i);
    end
end

figure()
subplot(2, 2, 1)
plot((no_inter_t(no_inter_idx(2:end)) - no_inter_t(no_inter_idx(1:end-1)))*1000)
grid on
ylim([0, 35])
ylabel('ms')
subplot(2, 2, 2)
plot((wi_inter_t(wi_inter_idx(2:end)) - wi_inter_t(wi_inter_idx(1:end-1)))*1000)
grid on
ylim([0, 35])
ylabel('ms')

subplot(2, 2, 3)
plot(no_inter_cumm_t)
subplot(2, 2, 4)
plot(wi_inter_cumm_t)



%% Functions
function ret_ary = sliding_window_var(sig_ary, win_size)
    [n_pkt, sig_len] = size(sig_ary);
    ret_ary = zeros(n_pkt, sig_len-win_size);
    
    for sig_idx = 1:n_pkt
        sig = sig_ary(sig_idx, :);
        ret = zeros(1, sig_len-win_size);
        for s_i = 1:sig_len-win_size
            sample = sig(s_i:s_i+win_size);
            ret(1, s_i) = mean(var(sample));
        end
        ret_ary(sig_idx, :) = ret;
    end

end

function [n_pkt, non_zero_ary] = calculate_num_packets(input_sig)
    n_pkt = 0;
    non_zero_ary = [];
    for i = 1:size(input_sig, 1)
        if input_sig(i, 1) ~= 0
            n_pkt = n_pkt + 1;
            non_zero_ary = [non_zero_ary, i];
        end
    end
end











































