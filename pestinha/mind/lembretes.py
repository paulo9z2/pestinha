"""
LEMBRETES (fork local 11/2026) — post-its com hora marcada (ex.: 19:00 = academia).

Regra fixa, não é decisão da rede: cada hora da pasta do pet (`lembretes.json`)
dispara uma vez por dia. Se o app estava fechado na hora certa, o aviso sai
atrasado quando ele abre (atrasado vale mais do que nunca). O estado
("o que já disparou hoje") fica na memória do pet, então reiniciar o app não
re-dispara o mesmo dia.

Exemplo (pets/katie/lembretes.json):
    [{"hora": "19:00", "texto": "Academia! Bora treinar, Paulo."}]
"""

import json
from datetime import datetime

from ..log import log


class Lembretes:
    """Post-its agendados: hora + texto fixo, um disparo por dia."""

    def __init__(self, arquivo, estado, debug, log_fn=log):
        """`arquivo` é o json com os horários; `estado` é o arquivo de memória."""
        self.arquivo = arquivo
        self.estado = estado
        self.debug = debug
        self.log = log_fn
        self.itens = self._carregar()

    def _carregar(self):
        """Lê a lista de horários; sem arquivo (ou inválido), não há lembretes."""
        try:
            raw = json.loads(self.arquivo.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return []
        itens = []
        for item in (raw if isinstance(raw, list) else []):
            if not isinstance(item, dict):
                continue
            hora = self._parse(item.get("hora"))
            texto = str(item.get("texto", "")).strip()
            if hora and texto:
                itens.append((hora, texto))
        if self.debug():
            self.log(f"[lembretes] {len(itens)} horário(s): "
                     f"{[f'{h[0]:02d}:{h[1]:02d}' for h, _ in itens]}")
        return itens

    @staticmethod
    def _parse(text):
        """'19:00' -> (19, 0); '19' -> (19, 0); qualquer outro formato -> None."""
        try:
            partes = str(text).strip().split(":")
            h = int(partes[0])
            m = int(partes[1]) if len(partes) > 1 else 0
        except (ValueError, IndexError):
            return None
        if 0 <= h <= 23 and 0 <= m <= 59:
            return (h, m)
        return None

    def devido(self, agora=None):
        """Devolve (hora, texto) de um lembrete vencido, ou None.

        Não marca ainda: o app marca só depois de mostrar o post-it com
        sucesso (sem espaço na tela, tenta de novo no próximo passo).
        """
        if not self.itens:
            return None
        agora = agora or datetime.now()
        feito = self._carregar_estado()
        for hora, texto in self.itens:
            if feito.get(f"{hora[0]:02d}:{hora[1]:02d}") == agora.date().isoformat():
                continue
            if (agora.hour, agora.minute) >= hora:       # cobre o catch-up depois de fechado
                return hora, texto
        return None

    def registrar(self, hora, agora=None):
        """Marca a hora como disparada hoje (só depois do post-it mostrar)."""
        agora = agora or datetime.now()
        feito = self._carregar_estado()
        feito[f"{hora[0]:02d}:{hora[1]:02d}"] = agora.date().isoformat()
        self._gravar_estado(feito)
        if self.debug():
            self.log(f"[lembretes] avisou {hora[0]:02d}:{hora[1]:02d}")

    def _carregar_estado(self):
        try:
            dados = json.loads(self.estado.read_text(encoding="utf-8"))
            return dados if isinstance(dados, dict) else {}
        except (OSError, ValueError):
            return {}

    def _gravar_estado(self, feito):
        try:
            self.estado.parent.mkdir(parents=True, exist_ok=True)
            self.estado.write_text(json.dumps(feito, ensure_ascii=False, indent=1),
                                   encoding="utf-8")
        except OSError:
            pass        # estado é conveniência: no pior caso re-dispara num reinício
