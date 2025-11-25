# Path to 40% Coverage

**Current:** 24.56%
**Target:** 40%
**Gap:** 15.44% (need ~900 more covered statements)

## Strategy: High-ROI Modules

Focus on modules with **high statement counts** and **low current coverage** for maximum coverage gain per test.

---

## Quick Win Targets (Ordered by Impact)

### 1. `common/install/installFonts.py` 📊
- **Statements:** 427
- **Current:** 0%
- **Target:** 50%
- **Gain:** ~213 statements = **+3.66% coverage**
- **Tests to add:**
  - Test font download with mocked HTTP requests
  - Test font installation to different directories
  - Test variant selection (Regular, Bold, Italic, etc.)
  - Test dry-run mode
  - Test error handling for missing fonts

### 2. `common/systems/validate.py` 📊
- **Statements:** 545
- **Current:** 39.63%
- **Target:** 60%
- **Gain:** ~111 statements = **+1.91% coverage**
- **Tests to add:**
  - Test `detectUnknownFields()` with nested objects
  - Test platform-specific field validation
  - Test error vs warning classification
  - Test main() function with different platforms

### 3. `common/systems/setupOrchestrator.py` 📊
- **Statements:** 316
- **Current:** 8.54%
- **Target:** 40%
- **Gain:** ~99 statements = **+1.70% coverage**
- **Tests to add:**
  - Test `executeStep()` with mocked actions
  - Test step state tracking
  - Test rollback session creation
  - Test resume prompt logic

### 4. `common/systems/status.py` 📊
- **Statements:** 275
- **Current:** 0%
- **Target:** 40%
- **Gain:** ~110 statements = **+1.89% coverage**
- **Tests to add:**
  - Test `checkGit()`, `checkZsh()`, `checkPackageManager()`
  - Test `checkInstalledApps()` with mocked package managers
  - Test `runStatusCheck()` with mocked system

### 5. `common/systems/verify.py` 📊
- **Statements:** 197
- **Current:** 0%
- **Target:** 40%
- **Gain:** ~79 statements = **+1.36% coverage**
- **Tests to add:**
  - Test package verification logic
  - Test Git config verification
  - Test font verification
  - Test `runVerification()` with mocked system

### 6. `common/install/installApps.py` 📊
- **Statements:** 184
- **Current:** 21.20%
- **Target:** 50%
- **Gain:** ~53 statements = **+0.91% coverage**
- **Tests to add:**
  - Test `installPackages()` with mocked package managers
  - Test parallel execution logic
  - Test `installFromConfig()` and `installFromConfigWithLinuxCommon()`
  - Test `runConfigCommands()` execution

### 7. `common/configure/configureGit.py` 📊
- **Statements:** 178
- **Current:** 9.55%
- **Target:** 40%
- **Gain:** ~54 statements = **+0.93% coverage**
- **Tests to add:**
  - Test `configureGitUser()` with dry-run
  - Test `configureGitDefaults()` with different configs
  - Test `configureGitLfs()` initialization
  - Test alias configuration

---

## Total Impact Calculation

| Module | Statements | Gain | Coverage Boost |
|--------|------------|------|----------------|
| installFonts | 213 | 50% → | +3.66% |
| validate | 111 | 60% → | +1.91% |
| setupOrchestrator | 99 | 40% → | +1.70% |
| status | 110 | 40% → | +1.89% |
| verify | 79 | 40% → | +1.36% |
| installApps | 53 | 50% → | +0.91% |
| configureGit | 54 | 40% → | +0.93% |
| **TOTAL** | **~719** | | **+12.36%** |

**Projected Coverage:** 24.56% + 12.36% = **36.92%**

To reach 40%, add a few more quick wins:
- Test `logging.py` functions (36% → 50%) = +3%
- Test `schemas.py` validation (48% → 65%) = +1%

**Final Projection:** ~40-41% coverage

---

## Implementation Plan

### Phase 1: Font Installation (Highest ROI)
**File:** `test/test/testInstallFonts.py`
- Mock HTTP requests for font downloads
- Test font variant parsing
- Test directory creation
- **Estimated:** 30-40 tests, 2-3 hours
- **Coverage gain:** +3.66%

### Phase 2: Validation & Status
**Files:** Add to existing validation tests, create `testStatus.py`, `testVerify.py`
- Expand validation.py tests
- Create status checking tests
- Create verification tests
- **Estimated:** 40-50 tests, 3-4 hours
- **Coverage gain:** +5.16%

### Phase 3: Setup Flow
**File:** `test/test/testSetupOrchestrator.py`
- Test step execution with mocks
- Test state management
- Test rollback logic
- **Estimated:** 20-30 tests, 2-3 hours
- **Coverage gain:** +1.70%

### Phase 4: Configuration Modules
**Files:** `testConfigureGit.py`, expand `testInstallApps.py`
- Test Git configuration logic
- Test app installation orchestration
- **Estimated:** 20-30 tests, 2 hours
- **Coverage gain:** +1.84%

### Phase 5: Polish
- Add logging tests
- Add schema tests
- Fill any remaining gaps
- **Estimated:** 10-20 tests, 1 hour
- **Coverage gain:** +2-3%

---

## Total Effort Estimate

**Total Time:** ~10-13 hours
**Total Tests:** ~120-170 additional tests
**Coverage Achievement:** 40-41%

**Current Status:** 24.56% with solid foundation
**Commit Target:** 40% with comprehensive coverage

---

## Recommended Approach

**Option A: Focus Sprint (Recommended)**
- Tackle Phase 1 (fonts) + Phase 2 (validation/status) = ~36% coverage
- This covers the most critical user-facing functionality
- **Time:** 5-7 hours
- **Result:** Solid coverage of critical paths

**Option B: Full Push to 40%**
- Complete all 5 phases
- **Time:** 10-13 hours
- **Result:** Comprehensive 40% coverage

**Option C: Incremental**
- Do Phase 1 now (fonts) → 28% coverage
- Commit and iterate
- **Time:** 2-3 hours per phase
- **Result:** Gradual improvement, frequent commits

---

## Notes

- All tests should use mocks for external dependencies (HTTP, subprocess, file I/O)
- Keep tests fast (< 0.1s each)
- Focus on happy paths and common error cases
- Skip edge cases for now (diminishing returns)
- Use fixtures for common test data

**The infrastructure is solid - now it's just adding tests!**
