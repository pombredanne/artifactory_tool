===============================
artifactory_tool
===============================

Artifactory Configurater and Maniuplator

* Free software: ISC license

Features
--------

Update your artifactory ldap settings

Usage
-----

To update or create repositories, you must have a directory with individual json files for each desired repository.  Then, point the tool at the directory, and it will create all the repos therein.  Each json file should be set up as per https://www.jfrog.com/confluence/display/RTF/Repository+Configuration+JSON

i.e:
`artifactory_tool --url http://artifactory.company.com --username admin --password password configure --repos_dir /tmp/repos`

Credits
---------

This package was created with Cookiecutter_ and the `audreyr/cookiecutter-pypackage`_ project template.

.. _Cookiecutter: https://github.com/audreyr/cookiecutter
.. _`audreyr/cookiecutter-pypackage`: https://github.com/audreyr/cookiecutter-pypackage
