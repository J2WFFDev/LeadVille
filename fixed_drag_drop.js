// CLEAN DRAG AND DROP IMPLEMENTATION - FIXED SYNTAX AND SCHEMA
async function dropOnTargetClean(ev) {
    ev.preventDefault();
    ev.currentTarget.style.backgroundColor = '';
    ev.currentTarget.style.borderColor = '';
    
    const deviceAddress = ev.dataTransfer.getData('device');
    const targetElement = ev.currentTarget;
    
    if (!deviceAddress) {
        console.log('❌ No device address found');
        return;
    }
    
    // Extract target number
    let targetId = targetElement.dataset.targetId || '1';
    console.log('🎯 CLEAN ASSIGNMENT:', deviceAddress, '→ Target', targetId);
    
    try {
        // Get current bridge config first
        const configResponse = await fetch('http://192.168.1.125:8001/api/admin/bridge/config');
        let currentConfig = { timer: null, sensors: [] };
        
        if (configResponse.ok) {
            const currentData = await configResponse.json();
            console.log('📋 Current config from API:', currentData);
            
            // Extract simple strings from complex API response
            currentConfig = {
                timer: currentData.timer?.address || null,
                sensors: currentData.sensors?.map(s => s.address || s) || []
            };
        }
        
        // Build updated config - SIMPLE SCHEMA for PUT request
        let updatedConfig = {
            timer: currentConfig.timer,
            sensors: [...currentConfig.sensors]  // Copy existing sensors
        };
        
        // Determine if device should be timer or sensor
        const isAMGTimer = deviceAddress.includes('C3:1F:DC:1A');
        
        if (isAMGTimer) {
            updatedConfig.timer = deviceAddress;
            console.log('⏱️ Assigning as TIMER:', deviceAddress);
        } else {
            // Add to sensors if not already there
            if (!updatedConfig.sensors.includes(deviceAddress)) {
                updatedConfig.sensors.push(deviceAddress);
                console.log('📡 Adding to SENSORS:', deviceAddress);
            }
        }
        
        console.log('📡 Sending SIMPLE config:', updatedConfig);
        
        // Send to API with correct URL and simple schema
        const updateResponse = await fetch('http://192.168.1.125:8001/api/admin/bridge/config', {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(updatedConfig)
        });
        
        if (updateResponse.ok) {
            const result = await updateResponse.json();
            console.log('✅ SUCCESS:', result);
            
            const deviceType = isAMGTimer ? 'Timer' : 'Sensor';
            alert(`✅ SUCCESS!\n\nDevice: ${deviceAddress}\nAssigned as: ${deviceType}\nTarget: ${targetId}\n\nPage will refresh to show changes.`);
            
            // Reload to show persistent changes
            setTimeout(() => window.location.reload(), 2000);
            
        } else {
            const errorText = await updateResponse.text();
            console.error('❌ API Error:', errorText);
            alert(`❌ ERROR: Failed to assign device\n\n${errorText}`);
        }
        
    } catch (error) {
        console.error('❌ Network Error:', error);
        alert(`❌ ERROR: Network problem\n\n${error.message}`);
    }
    
    // Reset visual feedback
    document.querySelectorAll('#paired-devices > div').forEach(d => {
        d.style.opacity = '1';
    });
}

// Initialize clean drag and drop - REPLACE ALL OTHER HANDLERS
function initializeCleanDragDrop() {
    console.log('🧹 Initializing CLEAN drag and drop...');
    
    // Remove any existing handlers first
    const targets = document.querySelectorAll('#targets-list > div');
    targets.forEach((target, index) => {
        // Clone node to remove all event listeners
        const newTarget = target.cloneNode(true);
        target.parentNode.replaceChild(newTarget, target);
        
        // Set target ID
        newTarget.dataset.targetId = index + 1;
        
        // Add drag event listeners
        newTarget.addEventListener('dragover', (e) => {
            e.preventDefault();
            e.currentTarget.style.backgroundColor = '#e0f2fe';
            e.currentTarget.style.borderColor = '#0284c7';
        });
        
        newTarget.addEventListener('dragleave', (e) => {
            e.currentTarget.style.backgroundColor = '';
            e.currentTarget.style.borderColor = '';
        });
        
        newTarget.addEventListener('drop', dropOnTargetClean);
    });
    
    console.log('✅ CLEAN drag and drop ready!', targets.length, 'targets updated');
}

// Start clean drag and drop after page loads
setTimeout(initializeCleanDragDrop, 12000);  // Wait for all other scripts to finish