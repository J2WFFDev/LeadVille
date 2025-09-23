import os
import subprocess
import shutil
import datetime

files = ['add_second_sensor.py','add_sensor_id.py','api_test.html','check_assignments.py','check_bridge_db.py','check_databases.py','check_db_detailed.py','check_db.py','check_sensors_schema.py','check_stage_assignments.py','clean_bridge_patch.py','cleanup_debug_logging.py','complete_sensor_fix.py','console_viewer_latest.py','console_viewer.py','create_bridge_table.py','create_main_bridge.py','create_simple_views.py','enhance_calibration_analysis.py','enhance_database_logging.py','enhance_impact_logging.py','enhance_multi_sensor.py','enhanced_amg_handler.py','example_database_usage.py','finalize_multi_sensor.py','fix_bridge_db.py','fix_bridge_ids.py','fix_calibration_handler.py','fix_calibration_processing.py','fix_calibration_progress.py','fix_database_config.py','fix_database_path.py','fix_dual_detectors.py','fix_dual_sensor_connect.py','fix_dual_sensor_notifications.py','fix_dynamic_sensors.py','fix_impact_logging.py','fix_logging_levels.py','fix_sensor_identification.py','fix_sensor_mac_scope.py','fix_sensor_target_caching.py','implement_complete_per_sensor_calibration.py','implement_per_sensor_calibration.py','import_stage_data.py','integration_demo.py','init_database_views.py','init_sensor_database_fixed.py','init_sensor_database.py']

os.makedirs('archive', exist_ok=True)
archive_list = 'archive/ARCHIVE_LIST.md'
if not os.path.exists(archive_list):
    with open(archive_list, 'w') as f:
        f.write('## Archive index\n\n')

with open(archive_list, 'a') as f:
    for fname in files:
        if os.path.exists(fname):
            try:
                subprocess.check_call(['git','ls-files','--error-unmatch',fname], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                subprocess.check_call(['git','mv',fname,'archive/'])
            except subprocess.CalledProcessError:
                shutil.move(fname, 'archive/')
            f.write(f"- {fname}: moved to archive on {datetime.datetime.utcnow().isoformat()}Z\n")

subprocess.call(['git','add',archive_list])
try:
    subprocess.check_call(['git','commit','-m','archive: move additional one-off scripts to archive/'])
except subprocess.CalledProcessError:
    pass
print('done')
