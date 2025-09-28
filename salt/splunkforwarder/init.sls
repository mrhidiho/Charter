{% from "splunkforwarder/map.jinja" import os_map %}

install_splunk_dependencies:
  pkg.installed:
    - pkgs: {{ os_map['pkgs'] }}

{% if pillar.get('auto_start_splunk', True) %}
start_splunk_forwarder:
  cmd.run:
    - name: 'echo "y" | /opt/splunkforwarder/bin/splunk start'
    - shell: /bin/bash
    - unless: '/opt/splunkforwarder/bin/splunk status | grep "is running"'
    - require:
      - pkg: install_splunk_dependencies
{% endif %}
