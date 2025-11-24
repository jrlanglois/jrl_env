Architecture Diagrams
=====================

Class Hierarchies
-----------------

Platform Hierarchy
~~~~~~~~~~~~~~~~~~

.. inheritance-diagram:: common.systems.platforms
   :parts: 1
   :caption: Platform class hierarchy showing all platform implementations

Package Manager Hierarchy
~~~~~~~~~~~~~~~~~~~~~~~~~~

.. inheritance-diagram:: common.install.packageManagers
   :parts: 1
   :caption: Package manager class hierarchy

Manager Classes
~~~~~~~~~~~~~~~

.. inheritance-diagram:: common.install.setupZsh common.install.androidStudio common.core.sudoHelper
   :parts: 1
   :caption: Manager classes (Zsh, OMZ, AndroidStudio, Sudo)

System Architecture
~~~~~~~~~~~~~~~~~~~

.. inheritance-diagram:: common.systems.systemBase common.systems.genericSystem
   :parts: 1
   :caption: System architecture base classes

Optional: Module Dependency Graphs
-----------------------------------

For advanced analysis, you can generate module dependency graphs using pydeps:

.. code-block:: bash

   # Install pydeps (optional)
   pip install pydeps

   # Generate dependency graph for entire project
   pydeps common --max-bacon=2 --cluster -o dependency_graph.svg

   # Generate for specific module
   pydeps common.systems.platforms --max-bacon=1 -o platforms_deps.svg

These graphs show:
- Module import relationships
- Dependency chains
- Circular dependencies (if any)
- Package structure

**Note:** This is optional - the class hierarchy diagrams below are generated automatically.

Class Relationships
-------------------

Key relationships in the architecture:

**Platform System:**

- ``BasePlatform`` (abstract) → ``MacOsPlatform``, ``WindowsPlatform``, ``UbuntuPlatform``, etc.
- Each platform owns its ``PackageManager`` instances
- Platforms delegate to managers for updates

**Manager Pattern:**

- ``ZshManager`` → Manages Zsh installation
- ``OhMyZshManager`` → Manages Oh My Zsh
- ``AndroidStudioManager`` → Manages Android SDK
- ``SudoManager`` → Manages elevated permissions

**Package Managers:**

- ``PackageManager`` (abstract) → All platform-specific implementations
- Each knows how to ``check()``, ``install()``, ``update()``, and ``updateAll()``
- Standardised error handling via ``runPackageCommand()``

Generating Diagrams
-------------------

**Prerequisites:**

Install Graphviz (required for diagram generation):

.. code-block:: bash

   # macOS
   brew install graphviz

   # Ubuntu/Debian
   sudo apt install graphviz

   # Windows
   choco install graphviz

**Generate Documentation:**

.. code-block:: bash

   python3 docs/generateDocs.py

This automatically generates:
- Class inheritance diagrams (embedded in pages)
- Interactive SVG diagrams
- Complete API documentation

**View Results:**

Open ``docs/_build/html/index.html`` in your browser and navigate to this "Architecture Diagrams" page.

The diagrams are interactive - zoom and click on classes to navigate to their documentation.
