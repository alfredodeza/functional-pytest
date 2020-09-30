def test_passwd_file(host):
    passwd = host.file("/etc/passwd")
    assert passwd.contains("root")
    assert passwd.user == "root"
    assert passwd.group == "wheel"
    assert passwd.mode == 0o644


def test_nginx_is_installed(host):
    nginx = host.package("nginx")
    assert nginx.is_installed is False
