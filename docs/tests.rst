Test Suite
==========

The ``test/`` directory contains comprehensive validation and testing scripts.

Overview
--------

The test suite validates:

- Platform detection logic
- Configuration file schemas
- Package availability
- Repository accessibility
- Git configuration
- Font availability
- Setup validation behaviour

All test scripts support ``--help`` and ``--quiet`` flags.

Validation Tests
----------------

validatePackages.py
~~~~~~~~~~~~~~~~~~~

Validates that packages exist in their respective package managers.

**Usage:**

.. code-block:: bash

   python3 test/validatePackages.py configs/macos.json
   python3 test/validatePackages.py configs/ubuntu.json

**Description:**

Checks each package in a platform config against the actual package manager to ensure:

- Package names are correct
- Packages are available for installation
- No typos or deprecated package names

**Supported Package Managers:**

- Homebrew (macOS)
- APT (Debian/Ubuntu)
- DNF (Fedora/RedHat)
- Pacman (Arch Linux)
- Winget (Windows)

validateLinuxCommonPackages.py
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Validates packages across all Linux package managers.

**Usage:**

.. code-block:: bash

   python3 test/validateLinuxCommonPackages.py configs/linuxCommon.json

**Description:**

Ensures packages in ``linuxCommon.json`` are available across all supported Linux distributions:

- APT (Debian/Ubuntu family)
- DNF (Fedora/RedHat)
- Pacman (Arch Linux)
- Zypper (OpenSUSE)

validateFonts.py
~~~~~~~~~~~~~~~~

Validates Google Fonts availability.

**Usage:**

.. code-block:: bash

   python3 test/validateFonts.py configs/fonts.json

**Description:**

Checks each font against the Google Fonts API to ensure:

- Font family names are correct
- Fonts are available for download
- No deprecated or removed fonts

validateRepositories.py
~~~~~~~~~~~~~~~~~~~~~~~

Validates repository accessibility.

**Usage:**

.. code-block:: bash

   python3 test/validateRepositories.py configs/repositories.json

**Description:**

Checks repository URLs and wildcard patterns:

- Repository URLs are accessible
- Wildcard patterns expand correctly
- GitHub API authentication works
- Rate limits are handled

validateGitConfig.py
~~~~~~~~~~~~~~~~~~~~

Validates Git configuration.

**Usage:**

.. code-block:: bash

   python3 test/validateGitConfig.py configs/gitConfig.json

**Description:**

Validates Git configuration for:

- User email format
- GitHub username format
- Alias syntax
- Default settings
- SSH key configuration

Unit Tests
----------

testPlatformDetection.py
~~~~~~~~~~~~~~~~~~~~~~~~

Tests platform detection logic.

**Usage:**

.. code-block:: bash

   python3 test/testPlatformDetection.py

**Description:**

Comprehensive unit tests for:

- Operating system detection
- Linux distribution identification
- Platform enum handling
- Edge cases and fallbacks

**Test Coverage:**

- 16 test cases
- All supported platforms
- Error handling

testUtilities.py
~~~~~~~~~~~~~~~~

Tests utility functions.

**Usage:**

.. code-block:: bash

   python3 test/testUtilities.py

**Description:**

Tests core utility functions from ``common/core/utilities.py``:

- Command existence checking
- JSON path extraction
- File operations
- Configuration helpers

testSetupValidation.py
~~~~~~~~~~~~~~~~~~~~~~

Tests setup validation behaviour.

**Usage:**

.. code-block:: bash

   python3 test/testSetupValidation.py

**Description:**

Validates that setup fails early and clearly when:

- Configuration files are missing
- Required dependencies are unavailable
- Invalid configurations are provided

testWildcardRepos.py
~~~~~~~~~~~~~~~~~~~~

Tests repository wildcard expansion.

**Usage:**

.. code-block:: bash

   python3 test/testWildcardRepos.py

**Description:**

Tests GitHub wildcard pattern expansion:

- Pattern parsing
- API authentication
- Caching behaviour
- Rate limit handling

Running All Tests
-----------------

Run the complete test suite:

.. code-block:: bash

   # Run all validation tests
   python3 test/validatePackages.py configs/macos.json
   python3 test/validateLinuxCommonPackages.py configs/linuxCommon.json
   python3 test/validateFonts.py configs/fonts.json
   python3 test/validateRepositories.py configs/repositories.json
   python3 test/validateGitConfig.py configs/gitConfig.json

   # Run all unit tests
   python3 test/testPlatformDetection.py
   python3 test/testUtilities.py
   python3 test/testSetupValidation.py
   python3 test/testWildcardRepos.py

Or use the validation system:

.. code-block:: bash

   # Validate all configurations
   python3 -m common.systems.validate

Continuous Integration
----------------------

All tests run automatically in CI via GitHub Actions:

- ``ci.yml`` - Linting and syntax checks
- ``validateConfigs.yml`` - Configuration validation across all platforms

See ``.github/workflows/`` for CI configuration.

See Also
--------

- :doc:`common.systems.validate` - Unified validation system
- :doc:`common.systems.schemas` - JSON schema definitions
- ``test/README.md`` - Detailed test documentation
