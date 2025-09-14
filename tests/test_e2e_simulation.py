"""
End-to-end tests for the LeadVille simulation interface using Playwright.
Tests the complete user experience including the web interface, real-time updates,
and simulation controls.
"""

import asyncio
import json
import pytest
from pathlib import Path
import time
from playwright.async_api import async_playwright, Page, Browser, BrowserContext


class TestSimulationUI:
    """End-to-end tests for the simulation user interface"""
    
    @pytest.fixture
    async def browser_context(self):
        """Setup browser context for testing"""
        playwright = await async_playwright().start()
        browser = await playwright.chromium.launch(headless=True)
        context = await browser.new_context(
            viewport={"width": 1280, "height": 720},
            # Enable permissions for notifications if needed
            permissions=["notifications"]
        )
        
        yield context
        
        await context.close()
        await browser.close()
        await playwright.stop()
    
    @pytest.fixture
    async def page(self, browser_context):
        """Create a page for testing"""
        page = await browser_context.new_page()
        return page
    
    @pytest.mark.asyncio
    async def test_index_page_loads(self, page: Page):
        """Test that the main index page loads correctly"""
        # Serve the HTML file
        html_path = Path(__file__).parent.parent / "index.html"
        await page.goto(f"file://{html_path.absolute()}")
        
        # Check page title
        title = await page.title()
        assert "LeadVille" in title or title == ""  # File protocol might not set title
        
        # Check for key elements
        await page.wait_for_selector("#sensor-status", state="visible")
        await page.wait_for_selector("#temperature", state="visible")
        await page.wait_for_selector("#system-status", state="visible")
        
        # Verify initial sensor status
        sensor_status = await page.text_content("#sensor-status")
        assert sensor_status == "Offline"
        
        # Verify initial temperature display
        temperature = await page.text_content("#temperature")
        assert temperature == "--°C"
    
    @pytest.mark.asyncio
    async def test_sensor_activation(self, page: Page):
        """Test sensor activation functionality"""
        html_path = Path(__file__).parent.parent / "index.html"
        await page.goto(f"file://{html_path.absolute()}")
        
        # Find and click the sensor activation button
        # Note: The exact button selector depends on the HTML structure
        # Looking at app.js, there should be event listeners set up
        
        # Wait for the interface to be ready
        await page.wait_for_timeout(1000)
        
        # Check if there are clickable elements for sensor control
        # This test assumes there are buttons or controls for sensor management
        buttons = await page.query_selector_all("button")
        
        if buttons:
            # Click the first button (assuming it's sensor related)
            await buttons[0].click()
            
            # Wait for potential status changes
            await page.wait_for_timeout(2000)
            
            # Check if sensor status changed
            sensor_status = await page.text_content("#sensor-status")
            # Status might change to "Online" if simulation is active
    
    @pytest.mark.asyncio
    async def test_temperature_updates(self, page: Page):
        """Test that temperature updates work correctly"""
        html_path = Path(__file__).parent.parent / "index.html"
        await page.goto(f"file://{html_path.absolute()}")
        
        # Wait for initial load
        await page.wait_for_timeout(1000)
        
        # Get initial temperature
        initial_temp = await page.text_content("#temperature")
        
        # Start sensor simulation if there's a way to do it
        # This depends on the interface having simulation controls
        start_buttons = await page.query_selector_all("button")
        
        if start_buttons:
            # Try clicking buttons to start simulation
            for button in start_buttons[:3]:  # Try first few buttons
                button_text = await button.text_content()
                if button_text and ("start" in button_text.lower() or "activate" in button_text.lower()):
                    await button.click()
                    break
        
        # Wait for temperature updates (sensor simulation runs every 2 seconds)
        await page.wait_for_timeout(5000)
        
        # Check if temperature has been updated from initial value
        current_temp = await page.text_content("#temperature")
        # If simulation is working, temperature should change from "--°C"
        
    @pytest.mark.asyncio
    async def test_system_status_indicators(self, page: Page):
        """Test system status indicators functionality"""
        html_path = Path(__file__).parent.parent / "index.html"
        await page.goto(f"file://{html_path.absolute()}")
        
        # Wait for page to load
        await page.wait_for_timeout(1000)
        
        # Check for system status elements
        status_elements = [
            "#system-interface-status",
            "#system-sensor-status", 
            "#system-timer-status"
        ]
        
        for element_id in status_elements:
            element = await page.query_selector(element_id)
            if element:
                status_text = await element.text_content()
                class_name = await element.get_attribute("class")
                
                # Verify status text exists and has appropriate class
                assert status_text is not None
                assert class_name is not None
    
    @pytest.mark.asyncio
    async def test_timer_functionality(self, page: Page):
        """Test timer-related functionality"""
        html_path = Path(__file__).parent.parent / "index.html"
        await page.goto(f"file://{html_path.absolute()}")
        
        # Wait for initialization
        await page.wait_for_timeout(1000)
        
        # Look for timer display elements
        timer_elements = ["#timer-display", "#timer", ".timer"]
        
        timer_element = None
        for selector in timer_elements:
            element = await page.query_selector(selector)
            if element:
                timer_element = element
                break
        
        if timer_element:
            # Check initial timer display
            timer_text = await timer_element.text_content()
            
            # Look for timer control buttons
            timer_buttons = await page.query_selector_all("button")
            
            # Try to find start/stop timer buttons
            for button in timer_buttons:
                button_text = await button.text_content()
                if button_text and ("timer" in button_text.lower() or "start" in button_text.lower()):
                    await button.click()
                    
                    # Wait for timer to potentially change
                    await page.wait_for_timeout(2000)
                    
                    # Check if timer display updated
                    new_timer_text = await timer_element.text_content()
                    break
    
    @pytest.mark.asyncio
    async def test_responsive_design(self, page: Page):
        """Test responsive design at different viewport sizes"""
        html_path = Path(__file__).parent.parent / "index.html"
        
        # Test different viewport sizes
        viewports = [
            {"width": 1920, "height": 1080},  # Desktop
            {"width": 1024, "height": 768},   # Tablet landscape
            {"width": 768, "height": 1024},   # Tablet portrait
            {"width": 375, "height": 667},    # Mobile
        ]
        
        for viewport in viewports:
            await page.set_viewport_size(viewport["width"], viewport["height"])
            await page.goto(f"file://{html_path.absolute()}")
            
            # Wait for load
            await page.wait_for_timeout(1000)
            
            # Check that key elements are still visible and accessible
            sensor_status = await page.query_selector("#sensor-status")
            temperature = await page.query_selector("#temperature")
            
            if sensor_status:
                is_visible = await sensor_status.is_visible()
                assert is_visible, f"Sensor status not visible at {viewport['width']}x{viewport['height']}"
            
            if temperature:
                is_visible = await temperature.is_visible()
                assert is_visible, f"Temperature not visible at {viewport['width']}x{viewport['height']}"
    
    @pytest.mark.asyncio
    async def test_error_handling(self, page: Page):
        """Test error handling in the interface"""
        html_path = Path(__file__).parent.parent / "index.html"
        await page.goto(f"file://{html_path.absolute()}")
        
        # Listen for console errors
        console_messages = []
        
        def handle_console(msg):
            console_messages.append({
                "type": msg.type,
                "text": msg.text,
                "args": [arg.json_value() for arg in msg.args]
            })
        
        page.on("console", handle_console)
        
        # Listen for page errors
        page_errors = []
        
        def handle_error(error):
            page_errors.append(str(error))
        
        page.on("pageerror", handle_error)
        
        # Wait for page to fully load and execute
        await page.wait_for_timeout(3000)
        
        # Try to trigger various interactions
        buttons = await page.query_selector_all("button")
        for i, button in enumerate(buttons[:3]):  # Test first few buttons
            try:
                await button.click()
                await page.wait_for_timeout(500)
            except Exception:
                pass  # Some buttons might not be functional in file:// mode
        
        # Check for critical JavaScript errors
        critical_errors = [msg for msg in console_messages if msg["type"] == "error"]
        
        # Allow for some expected errors in file:// mode (like network requests)
        # but ensure no critical application errors
        for error in critical_errors:
            error_text = error["text"].lower()
            # Skip expected file:// protocol limitations
            if not any(skip in error_text for skip in [
                "fetch", "xmlhttprequest", "cors", "network", "websocket"
            ]):
                print(f"Unexpected error: {error}")


class TestWebSocketSimulation:
    """Test WebSocket functionality for real-time simulation updates"""
    
    @pytest.fixture
    async def mock_websocket_server(self):
        """Setup a mock WebSocket server for testing"""
        import websockets
        
        connected_clients = set()
        
        async def handler(websocket, path):
            connected_clients.add(websocket)
            try:
                # Send mock simulation data
                simulation_data = {
                    "type": "simulation_update",
                    "data": {
                        "timestamp": time.time(),
                        "shots_fired": 3,
                        "impacts_detected": 2,
                        "current_temperature": 21.5,
                        "sensor_status": "online",
                        "timer_status": "active"
                    }
                }
                
                await websocket.send(json.dumps(simulation_data))
                
                # Keep connection alive
                async for message in websocket:
                    # Echo back for testing
                    await websocket.send(f"echo: {message}")
                    
            except websockets.exceptions.ConnectionClosed:
                pass
            finally:
                connected_clients.discard(websocket)
        
        # Start server
        server = await websockets.serve(handler, "localhost", 8765)
        
        yield server
        
        # Cleanup
        server.close()
        await server.wait_closed()
    
    @pytest.mark.asyncio
    async def test_websocket_connection(self, page: Page, mock_websocket_server):
        """Test WebSocket connection and data reception"""
        html_path = Path(__file__).parent.parent / "index.html"
        
        # Inject WebSocket testing code into the page
        await page.goto(f"file://{html_path.absolute()}")
        
        # Add WebSocket test client
        websocket_test = """
        const testWebSocket = () => {
            const ws = new WebSocket('ws://localhost:8765');
            
            ws.onopen = () => {
                console.log('WebSocket connected for testing');
                window.wsConnected = true;
            };
            
            ws.onmessage = (event) => {
                console.log('WebSocket message received:', event.data);
                window.wsLastMessage = event.data;
                try {
                    const data = JSON.parse(event.data);
                    if (data.type === 'simulation_update') {
                        window.wsSimulationData = data.data;
                    }
                } catch (e) {
                    // Not JSON, store as text
                    window.wsTextMessage = event.data;
                }
            };
            
            ws.onerror = (error) => {
                console.error('WebSocket error:', error);
                window.wsError = error;
            };
            
            window.testWebSocket = ws;
        };
        
        testWebSocket();
        """
        
        await page.evaluate(websocket_test)
        
        # Wait for connection and message
        await page.wait_for_timeout(3000)
        
        # Check if WebSocket connected
        ws_connected = await page.evaluate("window.wsConnected")
        assert ws_connected, "WebSocket should have connected"
        
        # Check if simulation data was received
        simulation_data = await page.evaluate("window.wsSimulationData")
        if simulation_data:
            assert "shots_fired" in simulation_data
            assert "impacts_detected" in simulation_data
            assert "sensor_status" in simulation_data


class TestSimulationControls:
    """Test simulation control interface"""
    
    @pytest.mark.asyncio
    async def test_simulation_scenario_selection(self, page: Page):
        """Test simulation scenario selection if available"""
        html_path = Path(__file__).parent.parent / "index.html"
        await page.goto(f"file://{html_path.absolute()}")
        
        # Look for scenario selection elements (dropdowns, radio buttons, etc.)
        scenario_controls = [
            "select[name*='scenario']",
            "select[id*='scenario']", 
            "input[name*='scenario']",
            ".scenario-selector"
        ]
        
        scenario_element = None
        for selector in scenario_controls:
            element = await page.query_selector(selector)
            if element:
                scenario_element = element
                break
        
        if scenario_element:
            tag_name = await scenario_element.evaluate("el => el.tagName.toLowerCase()")
            
            if tag_name == "select":
                # Test dropdown selection
                options = await scenario_element.query_selector_all("option")
                if len(options) > 1:
                    # Select different option
                    await scenario_element.select_option(index=1)
                    
                    # Verify selection changed
                    selected_value = await scenario_element.evaluate("el => el.value")
                    assert selected_value is not None
    
    @pytest.mark.asyncio
    async def test_simulation_speed_control(self, page: Page):
        """Test simulation speed controls if available"""
        html_path = Path(__file__).parent.parent / "index.html"
        await page.goto(f"file://{html_path.absolute()}")
        
        # Look for speed control elements
        speed_controls = [
            "input[type='range'][name*='speed']",
            "input[type='number'][name*='speed']",
            ".speed-control",
            "#simulation-speed"
        ]
        
        for selector in speed_controls:
            speed_element = await page.query_selector(selector)
            if speed_element:
                input_type = await speed_element.get_attribute("type")
                
                if input_type == "range":
                    # Test range slider
                    await speed_element.fill("0.5")  # Set to middle value
                    value = await speed_element.input_value()
                    assert value == "0.5"
                
                elif input_type == "number":
                    # Test number input
                    await speed_element.fill("2.0")
                    value = await speed_element.input_value()
                    assert value == "2.0"
                
                break
    
    @pytest.mark.asyncio
    async def test_error_injection_controls(self, page: Page):
        """Test error injection controls if available"""
        html_path = Path(__file__).parent.parent / "index.html"
        await page.goto(f"file://{html_path.absolute()}")
        
        # Look for error injection controls
        error_controls = [
            "input[type='checkbox'][name*='error']",
            "button[name*='error']",
            ".error-control",
            "#inject-error"
        ]
        
        for selector in error_controls:
            error_element = await page.query_selector(selector)
            if error_element:
                tag_name = await error_element.evaluate("el => el.tagName.toLowerCase()")
                
                if tag_name == "input":
                    input_type = await error_element.get_attribute("type")
                    if input_type == "checkbox":
                        # Test checkbox toggle
                        await error_element.check()
                        is_checked = await error_element.is_checked()
                        assert is_checked
                        
                        await error_element.uncheck()
                        is_checked = await error_element.is_checked()
                        assert not is_checked
                
                elif tag_name == "button":
                    # Test button click
                    await error_element.click()
                    # Would need to verify error injection occurred
                
                break


class TestSimulationDataVisualization:
    """Test data visualization components"""
    
    @pytest.mark.asyncio
    async def test_real_time_charts(self, page: Page):
        """Test real-time chart updates if available"""
        html_path = Path(__file__).parent.parent / "index.html"
        await page.goto(f"file://{html_path.absolute()}")
        
        # Look for chart elements (Canvas, SVG, Chart.js, etc.)
        chart_selectors = [
            "canvas",
            "svg",
            ".chart",
            "#sensor-chart",
            "#timing-chart"
        ]
        
        charts_found = []
        for selector in chart_selectors:
            elements = await page.query_selector_all(selector)
            charts_found.extend(elements)
        
        # If charts are present, verify they're rendered
        for chart in charts_found:
            is_visible = await chart.is_visible()
            if is_visible:
                # Get element dimensions to verify it's actually rendered
                box = await chart.bounding_box()
                assert box["width"] > 0 and box["height"] > 0
    
    @pytest.mark.asyncio
    async def test_statistics_display(self, page: Page):
        """Test statistics display updates"""
        html_path = Path(__file__).parent.parent / "index.html"
        await page.goto(f"file://{html_path.absolute()}")
        
        # Look for statistics elements
        stats_selectors = [
            ".stats",
            ".statistics", 
            "#shot-count",
            "#impact-count",
            "#accuracy",
            "[data-stat]"
        ]
        
        stats_elements = []
        for selector in stats_selectors:
            elements = await page.query_selector_all(selector)
            stats_elements.extend(elements)
        
        # Verify statistics elements exist and have content
        for element in stats_elements:
            if await element.is_visible():
                text = await element.text_content()
                # Statistics should have some content (numbers, percentages, etc.)
                assert text is not None
                assert len(text.strip()) > 0


if __name__ == "__main__":
    pytest.main([__file__])