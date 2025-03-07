clc;
clear;
close all;

% Attempt to initialize Pluto 1
disp('Attempting to initialize Pluto 1...');
try
    % Initialize Pluto 1 (first available device)
    txPluto2 = sdrtx('Pluto', 'RadioID', 'usb:0', ...  % Using first available USB device
                     'CenterFrequency', 325e6, ...
                     'BasebandSampleRate', 1e6, ...
                     'Gain', -10);
    disp('Transmitting 325 MHz signal using Pluto 1...');
catch ME
    disp(['Error with Pluto 1: ', ME.message]);
    disp('Attempting to initialize Pluto 2...');
    
    try
        % Initialize Pluto 2 (second available device)
        txPluto2 = sdrtx('Pluto', 'RadioID', 'usb:1', ...  % Using second available USB device
                         'CenterFrequency', 325e6, ...
                         'BasebandSampleRate', 1e6, ...
                         'Gain', -10);
        disp('Transmitting 325 MHz signal using Pluto 2...');
    catch ME2
        disp(['Error with Pluto 2: ', ME2.message]);
        return; % Exit if both Pluto devices cannot be initialized
    end
end

% Generate a baseband sine wave signal (100 kHz)
fs = 1e6;             % Sample rate
fBaseband = 100e3;    % Baseband frequency
t = (0:1023).'/fs;    % Time vector
signal = exp(1i*2*pi*fBaseband*t); % Complex sine wave (I + jQ)

% Transmit loop
while true
    try
        txPluto2(signal);  % Transmit signal
    catch ME2
        disp(['Transmission Error: ', ME2.message]);
    end
end

% Release the Pluto device after use
release(txPluto2);
