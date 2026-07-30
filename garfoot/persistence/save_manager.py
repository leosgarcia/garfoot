"""Gerenciador de leitura, escrita atômica e listagem de saves em disco."""

from __future__ import annotations

from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
from typing import Any

from garfoot.domain.game_state import GameState, SaveMetadata


class SaveError(Exception):
    """Erro base para operações do SaveManager."""


class InvalidSaveError(SaveError):
    """Lançada quando um arquivo de save está corrompido ou é inválido."""


def get_default_save_dir() -> Path:
    """Retorna o diretório padrão para gravações de save (~/.garfoot/saves/)."""

    home_dir = Path.home()
    save_dir = home_dir / ".garfoot" / "saves"
    try:
        save_dir.mkdir(parents=True, exist_ok=True)
        return save_dir
    except OSError:
        # Fallback para diretório local se home não for gravável
        local_dir = Path(__file__).resolve().parents[2] / "saves"
        local_dir.mkdir(parents=True, exist_ok=True)
        return local_dir


def slugify(text: str) -> str:
    """Converte um nome de save em um slug seguro para nome de arquivo."""

    clean = re.sub(r"[^\w\s-]", "", text.strip().lower())
    return re.sub(r"[-\s]+", "_", clean)


class SaveManager:
    """Gerencia a persistência de GameState no sistema de arquivos."""

    def __init__(self, save_dir: Path | None = None) -> None:
        self.save_dir = save_dir if save_dir is not None else get_default_save_dir()
        self.save_dir.mkdir(parents=True, exist_ok=True)

    def save_game(self, state: GameState, filename: str | None = None) -> Path:
        """Salva o GameState em disco usando escrita atômica (arquivo temporário + rename)."""

        if not state.saved_at:
            state.saved_at = datetime.now(timezone.utc).isoformat()

        if not filename:
            slug = slugify(state.save_name)
            filename = f"{slug}.json"

        target_path = self.save_dir / filename
        temp_path = self.save_dir / f"{filename}.tmp"

        data = state.to_dict()

        try:
            # Escrita atômica em arquivo temporário
            with open(temp_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            # Substituição atômica no sistema operacional
            os.replace(temp_path, target_path)
            return target_path
        except Exception as err:
            if temp_path.exists():
                try:
                    temp_path.unlink()
                except OSError:
                    pass
            raise SaveError(f"Falha ao salvar jogo em {target_path}: {err}") from err

    def load_game(self, path_or_filename: str | Path) -> GameState:
        """Carrega um GameState a partir de um arquivo em disco."""

        path = Path(path_or_filename)
        if not path.is_absolute():
            path = self.save_dir / path

        if not path.exists():
            raise InvalidSaveError(f"Arquivo de save não encontrado: {path}")

        try:
            content = path.read_text(encoding="utf-8")
            data = json.loads(content)
            return GameState.from_dict(data)
        except (json.JSONDecodeError, KeyError, ValueError, TypeError) as err:
            raise InvalidSaveError(f"Arquivo de save corrompido ou inválido ({path.name}): {err}") from err

    def list_saves(self) -> list[SaveMetadata]:
        """Lista todos os saves disponíveis no diretório com seus metadados resumidos."""

        saves: list[SaveMetadata] = []
        for file in sorted(self.save_dir.glob("*.json")):
            try:
                content = file.read_text(encoding="utf-8")
                data = json.loads(content)
                meta = SaveMetadata(
                    save_name=data.get("save_name", file.stem),
                    player_team_name=data.get("player_team_name", "Desconhecido"),
                    season_year=int(data.get("current_season", 2026)),
                    current_round=int(data.get("current_round", 1)),
                    saved_at=data.get("saved_at", ""),
                    filepath=str(file),
                )
                saves.append(meta)
            except Exception:
                # Ignora arquivos inválidos na listagem para não travar a UI
                continue

        # Ordena pelo horário do save mais recente
        return sorted(saves, key=lambda s: s.saved_at, reverse=True)
