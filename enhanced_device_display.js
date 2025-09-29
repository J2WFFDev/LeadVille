        // Enhanced displayPairedDevices with bridge assignment correlation
        async function displayPairedDevices(devices) {
            console.log('displayPairedDevices called with:', devices);
            const pairedDevicesEl = document.getElementById('paired-devices');
            const pairedCountEl = document.getElementById('paired-count');

            // Add null checks to prevent errors
            if (!pairedDevicesEl) {
                console.error('paired-devices element not found');
                return;
            }
            if (!pairedCountEl) {
                console.error('paired-count element not found');
                return;
            }

            pairedCountEl.textContent = `(${devices.length})`;

            if (devices.length === 0) {
                pairedDevicesEl.innerHTML = `
                    <div class="text-center py-4 text-gray-500 border-2 border-dashed border-gray-200 rounded-lg">
                        <span class="text-2xl block mb-1">📱</span>
                        <p class="text-sm">No paired devices</p>
                    </div>
                `;
                return;
            }

            // Get current bridge configuration to show assignments
            let bridgeConfig = { timer: null, sensors: [] };
            try {
                const bridgeResponse = await fetch('http://192.168.1.125:8001/api/admin/bridge/config');
                if (bridgeResponse.ok) {
                    const bridgeData = await bridgeResponse.json();
                    bridgeConfig = {
                        timer: bridgeData.timer?.address || null,
                        sensors: bridgeData.sensors?.map(s => s.address || s) || []
                    };
                    console.log('📋 Bridge assignments loaded:', bridgeConfig);
                }
            } catch (error) {
                console.warn('Could not load bridge config for assignments:', error);
            }

            const deviceElements = devices.map((device, index) => {
                console.log('Processing device:', device);

                // Device status mapping
                const statusMap = {
                    'connected': { icon: '🟢', text: 'Connected', color: 'text-green-600' },
                    'offline': { icon: '⚪', text: 'Never Connected', color: 'text-gray-600' },
                    'disconnected': { icon: '🔴', text: 'Disconnected', color: 'text-red-600' },
                    'unknown': { icon: '❓', text: 'Unknown', color: 'text-yellow-600' }
                };

                const status = statusMap[device.status] || statusMap.unknown;
                console.log('Device status mapping:', device.status, '->', status);

                // Battery display
                const batteryDisplay = device.battery ? `${device.battery}% 🔋` : 'Unknown ❓';
                console.log('Battery:', device.battery, '->', batteryDisplay);

                // RSSI display
                const rssiDisplay = device.rssi ? `${device.rssi} dBm` : 'N/A ❓';
                console.log('RSSI:', device.rssi, '->', rssiDisplay);

                // Enhanced target assignment - check bridge config
                let targetDisplay = '🎯 Unassigned';
                let assignmentClass = 'text-gray-600';
                
                if (bridgeConfig.timer === device.address) {
                    targetDisplay = '⏱️ Timer (Assigned)';
                    assignmentClass = 'text-green-600 font-semibold';
                } else if (bridgeConfig.sensors.includes(device.address)) {
                    targetDisplay = '📡 Sensor (Assigned)';
                    assignmentClass = 'text-green-600 font-semibold';
                }
                
                console.log('Target assignment:', device.address, '->', targetDisplay);
                return `
                    <div class="flex items-center justify-between p-4 border rounded-lg hover:bg-gray-50 transition-colors" data-address="${device.address}">
                        <div class="flex items-center space-x-3">
                            <div class="text-2xl">📡</div>
                            <div>
                                <div class="font-medium">${device.label || "Unknown Device"}</div>
                                <div class="text-sm text-gray-600">${device.address}</div>
                                <div class="text-xs text-gray-500">ID: ${device.id} • ${device.type}</div>
                            </div>
                        </div>
                        <div class="text-right space-y-1">
                            <div class="flex items-center space-x-4">
                                <div class="text-xs">
                                    <span class="${status.color}">${status.icon}</span>
                                    <span class="ml-1 ${status.color}">${status.text}</span>
                                </div>
                                <div class="text-xs text-gray-500">
                                    Battery: ${batteryDisplay}
                                </div>
                            </div>
                            <div class="text-xs text-gray-500">
                                RSSI: ${rssiDisplay}
                            </div>
                            <div class="text-xs ${assignmentClass}">
                                ${targetDisplay}
                            </div>
                        </div>
                    </div>
                `;
            }).join("");

            pairedDevicesEl.innerHTML = deviceElements;
        }
