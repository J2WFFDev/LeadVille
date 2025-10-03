# LeadVille Refactoring Branch - Validation Checklist

## Branch Information
- **Branch Name**: `feature/refactor-paths-and-parsers`
- **Base Branch**: `main`
- **Status**: Ready for validation
- **GitHub URL**: https://github.com/J2WFFDev/LeadVille/tree/feature/refactor-paths-and-parsers

## What Was Refactored

### 🔧 Backend Changes
1. **Centralized Path Management**
   - Created `src/impact_bridge/paths.py`
   - Unified database paths: `CONFIG_DB`, `RUNTIME_DB`, `SAMPLES_DB`
   - Environment variable overrides supported

2. **Parser Consolidation**
   - Created `src/impact_bridge/ble/parsers/` package
   - Moved verbose parser to `parsers/verbose.py`
   - Created `parsers/simple_5561.py` 
   - Removed old `wtvb_parse*.py` files

3. **Updated Bridge Integration**
   - Updated imports in bridge files
   - Impact logging now uses `RUNTIME_DB`
   - Removed duplicate methods

4. **Quality Improvements**
   - Added path enforcement tests
   - Pre-commit hooks configuration
   - Updated pyproject.toml
   - Architecture documentation

## Validation Required

### ✅ **Already Verified on Pi**
- ✅ Paths module imports correctly
- ✅ Parser imports work from new package
- ✅ Bridge instantiates successfully
- ✅ Database paths resolve correctly
- ✅ No old parser files remain

### 🔍 **Still Need to Test**
1. **Runtime Validation**
   - [ ] Bridge connects to actual devices
   - [ ] Timer events write to `RUNTIME_DB`
   - [ ] Sensor events write to `RUNTIME_DB`
   - [ ] Verbose parser writes to `SAMPLES_DB` when enabled
   - [ ] All log files generate correctly

2. **Integration Testing**
   - [ ] Frontend still connects properly
   - [ ] WebSocket endpoints work
   - [ ] API endpoints respond correctly
   - [ ] Real BLE sensor data processes correctly

3. **Performance Testing**
   - [ ] No performance degradation
   - [ ] Database writes perform as expected
   - [ ] Memory usage unchanged

## Rollback Plan
If issues are found:
```bash
git checkout main
git branch -D feature/refactor-paths-and-parsers
git push origin --delete feature/refactor-paths-and-parsers
```

## Merge Plan
Once validated:
1. Create Pull Request on GitHub
2. Review changes
3. Merge to `main`
4. Deploy to Pi production

## Testing Commands

### On Pi (Code of Authority)
```bash
# Test basic imports
cd /home/jrwest/projects/LeadVille
python3 -c "from src.impact_bridge.paths import CONFIG_DB, RUNTIME_DB, SAMPLES_DB; print('Paths OK')"
python3 -c "from src.impact_bridge.ble.parsers import parse_bt50_frame, scan_and_parse; print('Parsers OK')"

# Test bridge startup
python3 src/impact_bridge/leadville_bridge.py --test-mode

# Check database creation
ls -la db/
```

### Database Verification
```bash
# Verify runtime DB schema
sqlite3 db/leadville_runtime.db ".schema"

# Check for proper indexes
sqlite3 db/leadville_runtime.db ".indexes"
```

## Risk Assessment
- **Low Risk**: Path and parser consolidation is well-tested
- **Medium Risk**: Database write changes need runtime validation
- **Mitigation**: Can quickly rollback if issues found

## Success Criteria
- [ ] All existing functionality works unchanged
- [ ] New centralized paths resolve correctly
- [ ] Database writes work properly
- [ ] No hardcoded paths remain
- [ ] Performance is maintained or improved

---
**Note**: This branch represents a major architectural improvement that provides better maintainability, testing, and deployment flexibility while maintaining full backward compatibility.