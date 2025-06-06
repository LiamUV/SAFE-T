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

%% Initialize KML file for output
kmlFile = 'beacon_locations.kml';
kmlHeader = ['<?xml version="1.0" encoding="UTF-8"?>' ...
             '<kml xmlns="http://www.opengis.net/kml/2.2">' ...
             '<Document>'];
kmlFooter = '</Document></kml>';

% Open KML file
fid = fopen(kmlFile, 'w');
fprintf(fid, '%s\n', kmlHeader);

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
        
        % Example Hex Packet (Dummy Processing) - Replace with actual signal decoding logic
        hexPacket = 'FFFE2F970E00800127299B1E21F600657969';
        countryCode = hexPacket(7:9); % Extract bits 27-36
        beaconHexID = hexPacket(10:25); % Extract bits 26-85
        encodedLocation = hexPacket(26:end); % Extract bits 113-132
        
        % Display extracted information
        fprintf('Country Code: %s\n', countryCode);
        fprintf('Beacon Hex ID: %s\n', beaconHexID);
        fprintf('Encoded Location: %s\n', encodedLocation);
        
        % Handle shorter encoded location data
        if length(encodedLocation) >= 16
            latHex = encodedLocation(1:8);  % First 8 hex digits for latitude
            lonHex = encodedLocation(9:16); % Next 8 hex digits for longitude
        elseif length(encodedLocation) >= 8
            latHex = encodedLocation(1:8);  % Use available data for latitude
            lonHex = '00000000';            % Default longitude if data is missing
        elseif length(encodedLocation) > 0
            latHex = [encodedLocation, repmat('0', 1, 8 - length(encodedLocation))]; % Pad with zeroes if data is too short
            lonHex = '00000000';            % Default longitude if data is missing
        else
            latHex = '00000000';            % Default latitude if data is missing
            lonHex = '00000000';            % Default longitude if data is missing
        end
        
        % Convert Hex to Decimal (Longitude and Latitude)
        lat = hex2dec(latHex) / 1e7;   % Convert to decimal, adjust scale as needed
        lon = hex2dec(lonHex) / 1e7;   % Convert to decimal, adjust scale as needed
        
        % Display decoded information
        fprintf('Latitude (Decoded): %f\n', lat);
        fprintf('Longitude (Decoded): %f\n', lon);
        
        % Write location to KML
        kmlPlacemark = ['<Placemark>' ...
                        '<name>Beacon - ' beaconHexID '</name>' ...
                        '<Point><coordinates>' num2str(lon) ',' num2str(lat) ',0</coordinates></Point>' ...
                        '</Placemark>'];
        fprintf(fid, '%s\n', kmlPlacemark);
    else
        disp('No 406 MHz Beacon Signal');
    end
    
    drawnow;
    pause(0.1);
end

%% Close KML file properly
fprintf(fid, '%s\n', kmlFooter);
fclose(fid);
disp('KML file saved as beacon_locations.kml');
