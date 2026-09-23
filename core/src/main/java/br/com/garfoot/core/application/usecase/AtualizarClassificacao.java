package br.com.garfoot.core.application.usecase;

import br.com.garfoot.core.model.campeonato.Campeonato;
import br.com.garfoot.core.model.campeonato.ClassificacaoItem;
import br.com.garfoot.core.model.partida.Partida;
import br.com.garfoot.core.model.partida.StatusPartida;

import java.util.Comparator;
import java.util.HashMap;
import java.util.Map;
import java.util.Objects;
import java.util.UUID;

public final class AtualizarClassificacao {
    public Campeonato executar(Campeonato campeonato) {
        Objects.requireNonNull(campeonato, "campeonato must not be null");
        Map<UUID, Estatisticas> tabela = new HashMap<>();
        campeonato.participantes().forEach(clube -> tabela.put(clube.id(), new Estatisticas(clube)));
        for (var rodada : campeonato.rodadas()) {
            for (Partida partida : rodada.partidas()) {
                if (partida.status() == StatusPartida.ENCERRADA) {
                    tabela.get(partida.mandante().id()).registrar(partida.golsMandante(), partida.golsVisitante());
                    tabela.get(partida.visitante().id()).registrar(partida.golsVisitante(), partida.golsMandante());
                }
            }
        }
        campeonato.atualizarClassificacao(tabela.values().stream().map(Estatisticas::item)
                .sorted(Comparator.comparingInt(ClassificacaoItem::pontos).reversed()
                        .thenComparing(Comparator.comparingInt(ClassificacaoItem::saldoGols).reversed())
                        .thenComparing(Comparator.comparingInt(ClassificacaoItem::golsPro).reversed())
                        .thenComparing(Comparator.comparingInt(ClassificacaoItem::vitorias).reversed())
                        .thenComparing(item -> item.clube().nome())
                        .thenComparing(item -> item.clube().id().toString())).toList());
        return campeonato;
    }

    private static final class Estatisticas {
        private final br.com.garfoot.core.model.clube.Clube clube;
        private int pontos, vitorias, empates, derrotas, golsPro, golsContra;
        private Estatisticas(br.com.garfoot.core.model.clube.Clube clube) { this.clube = clube; }
        private void registrar(int feitos, int sofridos) {
            golsPro += feitos; golsContra += sofridos;
            if (feitos > sofridos) { vitorias++; pontos += 3; }
            else if (feitos == sofridos) { empates++; pontos++; }
            else derrotas++;
        }
        private ClassificacaoItem item() {
            return new ClassificacaoItem(clube, pontos, vitorias, empates, derrotas, golsPro, golsContra);
        }
    }
}
