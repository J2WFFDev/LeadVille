function dropOnTarget(ev) {
    ev.preventDefault();
    ev.currentTarget.style.backgroundColor = '';
    ev.currentTarget.style.borderColor = '';

    const deviceAddress = ev.dataTransfer.getData('device');
    const targetId = ev.currentTarget.dataset.targetId;

    if (deviceAddress && targetId) {
        console.log('🎯 ASSIGNMENT with API:', deviceAddress, 'to Target', targetId);
        
        // Make the API call to persist the assignment
        persistAssignment(deviceAddress, targetId);

        // Update the target display immediately for user feedback
        const targetInfo = ev.currentTarget.querySelector('.font-medium');
        if (targetInfo && targetInfo.textContent.includes('No sensor assigned')) {
            targetInfo.textContent = deviceAddress + ' (Assigned)';
            targetInfo.className = 'font-medium text-green-600';
        }
    }

    // Reset device opacity
    document.querySelectorAll('#paired-devices > div').forEach(d => {
        d.style.opacity = '1';
    });
}

// Function to persist assignment via API
async function persistAssignment(deviceAddress, targetId) {
    try {
        // Get current bridge configuration
        const configResponse = await fetch('http://192.168.1.125:8001/api/admin/bridge/config');
        let currentConfig = { timer: null, sensors: [] };
        
        if (configResponse.ok) {
            const currentData = await configResponse.json();
            // Extract simple strings from complex API response
            currentConfig = {
                timer: currentData.timer?.address || null,
                sensors: currentData.sensors?.map(s => s.address || s) || []
            };
        }
        
        // Build updated config with simple schema
        let updatedConfig = {
            timer: currentConfig.timer,
            sensors: [...currentConfig.sensors]
        };
        
        // Determine if device should be timer or sensor
        const isAMGTimer = deviceAddress.includes('C3:1F:DC:1A');
        
        if (isAMGTimer) {
            updatedConfig.timer = deviceAddress;
            console.log('⏱️ Assigning as TIMER:', deviceAddress);
        } else {
            if (!updatedConfig.sensors.includes(deviceAddress)) {
                updatedConfig.sensors.push(deviceAddress);
                console.log('📡 Adding to SENSORS:', deviceAddress);
            }
        }
        
        console.log('📡 Persisting config:', updatedConfig);
        
        // Send to PUT endpoint with correct simple schema
        const updateResponse = await fetch('http://192.168.1.125:8001/api/admin/bridge/config', {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(updatedConfig)
        });
        
        if (updateResponse.ok) {
            const result = await updateResponse.json();
            console.log('✅ PERSISTED:', result);
            const deviceType = isAMGTimer ? 'Timer' : 'Sensor';
            alert(`✅ SUCCESS!\n\nDevice: ${deviceAddress}\nAssigned as: ${deviceType}\nTarget: ${targetId}\n\nAssignment saved permanently!`);
        } else {
            const errorText = await updateResponse.text();
            console.error('❌ Persist Error:', errorText);
            alert(`❌ ERROR: Failed to save assignment\n\n${errorText}`);
        }
        
    } catch (error) {
        console.error('❌ Persist Network Error:', error);
        alert(`❌ ERROR: Network problem\n\n${error.message}`);
    }
}