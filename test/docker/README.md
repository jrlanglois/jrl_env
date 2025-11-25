# Docker Testing for jrl_env

Test jrl_env across different Linux distributions using Docker containers.

## Quick Start

```bash
# Interactive Ubuntu shell
./test/docker/testInDocker.sh ubuntu shell

# Inside container (fresh system with only git):
./setup.sh  # Bootstraps Python, then runs full setup
# Or manually:
bash setup.sh --install --verbose 2>&1 | tee ~/setup.log
# Inspect logs, debug, iterate...
```

## Usage

```bash
./test/docker/testInDocker.sh <distro> [command] [options]
```

### Distributions

- `all` - Test all distributions
- `alpine` - Alpine Linux
- `arch` - Arch Linux
- `fedora` - Fedora 40
- `ubuntu` - Ubuntu 24.04 LTS

### Commands

**`shell` (default)** - Interactive bash shell
```bash
./test/docker/testInDocker.sh ubuntu shell

# Inside container, manually run:
python3 setup.py --install --dryRun
python3 setup.py --install --verbose 2>&1 | tee ~/setup.log
cat ~/setup.log  # Inspect logs
```

**`test`** - Automated dry-run test
```bash
./test/docker/testInDocker.sh ubuntu test
./test/docker/testInDocker.sh all test
```

**`validate`** - Run config validation
```bash
./test/docker/testInDocker.sh ubuntu validate
./test/docker/testInDocker.sh all validate
```

**`install`** - Full installation (not dry-run)
```bash
# Careful - this actually installs packages!
./test/docker/testInDocker.sh ubuntu install
```

### Options

- `--verbose` - Enable verbose output
- `--no-cache` - Rebuild Docker image from scratch

## Debugging Workflow

### 1. Interactive Testing

```bash
# Start interactive container
./test/docker/testInDocker.sh ubuntu shell

# Inside container:
python3 setup.py --install --verbose 2>&1 | tee ~/setup.log

# If it fails:
cat ~/setup.log                           # Check logs
cat logs/setup_ubuntu_*.log               # Check detailed logs
python3 -m common.systems.validate        # Validate configs
python3 -m common.systems.status          # Check what's installed
```

### 2. Iterative Development

```bash
# Your code is mounted as a volume - edits persist!
./test/docker/testInDocker.sh ubuntu shell

# Inside:
python3 setup.py --install --dryRun  # Test
# Exit container

# Edit code on your host machine
vim common/systems/platforms.py

# Re-run in fresh container
./test/docker/testInDocker.sh ubuntu shell
# Your changes are already there!
```

### 3. Save Breakpoints

```bash
# Run without --rm to save state
docker run -it --name jrl-debug \
  -v $(pwd):/home/testuser/jrl_env \
  jrl-env-test:ubuntu bash

# Make changes, debug, break things...
# Exit

# Save state
docker commit jrl-debug jrl-env-test:ubuntu-debug

# Later: restore exact state
docker run -it --rm jrl-env-test:ubuntu-debug bash
```

## Test All Distributions

```bash
# Quick validation on all distros
./test/docker/testInDocker.sh all validate

# Dry-run test on all distros
./test/docker/testInDocker.sh all test --verbose
```

## Manual Docker Commands

If you prefer manual control:

```bash
# Build image
docker build -t jrl-env-test:ubuntu -f test/docker/Dockerfile.ubuntu .

# Interactive shell
docker run -it --rm -v $(pwd):/home/testuser/jrl_env jrl-env-test:ubuntu bash

# One-off test
docker run --rm -v $(pwd):/home/testuser/jrl_env jrl-env-test:ubuntu \
  bash -c "python3 setup.py --install --dryRun"
```

## Cleanup

```bash
# Remove all test images
docker rmi jrl-env-test:ubuntu jrl-env-test:fedora jrl-env-test:arch jrl-env-test:alpine

# Remove stopped containers
docker container prune
```

## Tips

- **Logs persist** on your host in `logs/` (mounted volume)
- **Code changes** are instant (mounted volume, no rebuild needed)
- **Fast iterations** - containers start in ~2 seconds
- **Clean slate** every time (use `--rm`)

## Integration with CI

These Dockerfiles can also be used in GitHub Actions:

```yaml
jobs:
  test-ubuntu:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Test in Docker
        run: ./test/docker/testInDocker.sh ubuntu test
```

## Troubleshooting

**"Permission denied" errors:**
- Containers run as `testuser` (non-root) to match real usage
- sudo is configured with NOPASSWD for testing

**"Module not found" errors:**
- Make sure you're running from `/home/testuser/jrl_env`
- Code is mounted at that path

**"Docker not found":**
- Install Docker Desktop: https://www.docker.com/products/docker-desktop/
- Or Docker Engine on Linux: `sudo apt install docker.io`
