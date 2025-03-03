clc;
clear;
close all;

%% Initialize the ADALM Pluto Receiver
rxPluto = sdrrx('Pluto', 'CenterFrequency', 100e6, ...   % Set to a default frequency (e.g., 100 MHz)
                'BasebandSampleRate', 1e6, ...         % Set sample rate
                'SamplesPerFrame', 1024, ...           % Number of samples per frame
                'GainSource', 'AGC Fast Attack', ...   % Automatic Gain Control
                'OutputDataType', 'double');          % Output data type

%% Setup Plot
figure;
h = plot(nan, nan); 
title('Received Signal'); 
xlabel('Sample Index');
ylabel('Amplitude');
grid on;

%% Real-Time Signal Reception and Plotting Loop
while true
    % Receive signal
    signal = rxPluto();
    
    % Update Plot with Received Signal
    set(h, 'XData', 1:length(signal), 'YData', real(signal)); % Use real part of the signal
    drawnow;
    
    % Display simple message if signal detected
    if max(abs(signal)) > 0.1
        disp('Signal Detected!');
    else
        disp('No Signal');
    end
    
    % Pause to allow real-time plotting
    pause(0.1);
end
