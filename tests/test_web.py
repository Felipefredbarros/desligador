"""Página do celular: o PIN nunca fica guardado no navegador (docs/decisoes/0005)."""

from pathlib import Path

WEB = Path(__file__).resolve().parent.parent / "src" / "desligador" / "web"
APP = (WEB / "app.js").read_text(encoding="utf-8")
HTML = (WEB / "index.html").read_text(encoding="utf-8")


def test_pin_nao_vai_para_o_armazenamento_do_navegador():
    assert "setItem" not in APP and "getItem" not in APP
    assert "lembrar" not in HTML.lower()


def test_apaga_o_pin_que_versoes_antigas_guardavam():
    assert 'const PIN_ANTIGO = "desligador.pin"' in APP
    assert "localStorage.removeItem(PIN_ANTIGO)" in APP


def test_pin_so_e_enviado_no_login():
    assert APP.count("{ pin:") == 1
    assert '"/api/entrar"' in APP
