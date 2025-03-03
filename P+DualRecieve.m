clc;
clear;
close all;

%% Initialize Pluto+ SDR for Dual-Channel Reception
rxPluto = sdrrx('Pluto', ...
    'BasebandSampleRate', 1e6, ...
    'SamplesPerFrame', 4096, ...
    'GainSource', 'AGC Slow Attack', ...
    'OutputDataType', 'double', ...
    'ChannelMapping', 1);  % Single channel, switched between frequencies

%% Setup Plot
figure;
h1 = subplot(2,1,1); % First plot for 325 MHz
plot1 = plot(nan, nan);
title(h1, '325 MHz Signal');
xlabel(h1, 'Sample Index');
ylabel(h1, 'Amplitude');
grid on;

h2 = subplot(2,1,2); % Second plot for 406.025 MHz
plot2 = plot(nan, nan);
title(h2, '406.025 MHz Signal');
xlabel(h2, 'Sample Index');
ylabel(h2, 'Amplitude');
grid on;

%% Real-Time Signal Reception and Processing Loop
while true
    %% Receive 325 MHz signal
    rxPluto.CenterFrequency = 325e6;
    signal325 = rxPluto();
    
    % Update 325 MHz plot
    set(plot1, 'XData', 1:length(signal325), 'YData', real(signal325));
    
    % Detect 325 MHz signal
    if max(abs(signal325)) > 0.1
        disp('325 MHz Signal Detected!');
    else
        disp('No 325 MHz Signal');
    end
    
    %% Receive 406.025 MHz signal
    rxPluto.CenterFrequency = 406.025e6;
    signal406 = rxPluto();
    
    % Update 406 MHz plot
    set(plot2, 'XData', 1:length(signal406), 'YData', real(signal406));
    
    % Detect and Decode 406 MHz Signal
    if max(abs(signal406)) > 0.5
        disp('406 MHz Beacon Detected!');
        
        % Example Hex Packet (Dummy Processing)
        hexPacket = 'FFFE2F970E00800127299B1E21F600657969';
        countryCode = hexPacket(7:9); % Extract bits 27-36
        beaconHexID = hexPacket(10:25); % Extract bits 26-85
        encodedLocation = hexPacket(26:31); % Extract bits 113-132
        
        % Display Information
        fprintf('Country Code: %s\n', countryCode);
        fprintf('Beacon Hex ID: %s\n', beaconHexID);
        fprintf('Encoded Location: %s\n', encodedLocation);
    else
        disp('No 406 MHz Beacon Signal');
    end
    
    drawnow;
    pause(0.1);
end
