"""
Testes dos post-its agendados (fork local 11/2026): módulo puro, sem Qt.

Rodar (na pasta do projeto):  python -m pytest tests -q
"""

import json
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from pestinha.mind.lembretes import Lembretes  # noqa: E402

NUNCA = lambda: False  # noqa: E731


def make(tmp_path, items):
    arq = tmp_path / "lembretes.json"
    arq.write_text(json.dumps(items, ensure_ascii=False), encoding="utf-8")
    est = tmp_path / "mem" / "lembretes.json"
    return Lembretes(arq, est, NUNCA)


def test_sem_arquivo_nao_avis(tmp_path):
    l = Lembretes(tmp_path / "inexistente.json", tmp_path / "estado.json", NUNCA)
    assert l.itens == []
    assert l.devido(datetime(2026, 11, 25, 19, 0)) is None


def test_dispara_na_hora(tmp_path):
    l = make(tmp_path, [{"hora": "19:00", "texto": "Academia!"}])
    assert l.devido(datetime(2026, 11, 25, 18, 59)) is None
    assert l.devido(datetime(2026, 11, 25, 19, 0)) == ((19, 0), "Academia!")


def test_nao_repete_no_mesmo_dia(tmp_path):
    l = make(tmp_path, [{"hora": "19:00", "texto": "Academia!"}])
    hora, _ = l.devido(datetime(2026, 11, 25, 19, 0))
    l.registrar(hora, datetime(2026, 11, 25, 19, 0))
    assert l.devido(datetime(2026, 11, 25, 19, 5)) is None
    # dia seguinte dispara de novo
    assert l.devido(datetime(2026, 11, 26, 19, 0)) == ((19, 0), "Academia!")


def test_estado_sobrevive_ao_reinicio(tmp_path):
    l = make(tmp_path, [{"hora": "19:00", "texto": "Academia!"}])
    l.registrar((19, 0), datetime(2026, 11, 25, 19, 0))
    # novo processo, mesmos caminhos: não re-dispara no mesmo dia
    l2 = make(tmp_path, [{"hora": "19:00", "texto": "Academia!"}])
    assert l2.devido(datetime(2026, 11, 25, 21, 30)) is None


def test_relate_apos_atraso(tmp_path):
    """App fechado às 19:00, abriu às 20:10: o aviso sai atrasado, mas sai."""
    l = make(tmp_path, [{"hora": "19:00", "texto": "Academia!"}])
    assert l.devido(datetime(2026, 11, 25, 20, 10)) == ((19, 0), "Academia!")


def test_antes_da_hora_de_manha_nao_avis(tmp_path):
    l = make(tmp_path, [{"hora": "19:00", "texto": "Academia!"}])
    l.registrar((19, 0), datetime(2026, 11, 25, 19, 0))
    assert l.devido(datetime(2026, 11, 26, 8, 0)) is None


def test_horario_invalido_ignorado(tmp_path):
    l = make(tmp_path, [{"hora": "25:99", "texto": "x"},
                        {"hora": "19:00", "texto": "ok"},
                        {"texto": "sem hora"}])
    assert l.itens == [((19, 0), "ok")]


def test_hora_sem_minutos(tmp_path):
    l = make(tmp_path, [{"hora": "9", "texto": "café"}])
    assert l.devido(datetime(2026, 11, 25, 9, 1)) == ((9, 0), "café")
