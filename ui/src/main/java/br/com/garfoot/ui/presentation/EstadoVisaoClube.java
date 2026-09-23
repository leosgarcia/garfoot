package br.com.garfoot.ui.presentation;

import java.util.List;

public record EstadoVisaoClube(
        Status status,
        String nomeClube,
        List<String> elenco,
        String proximaPartida,
        List<String> classificacao,
        String ultimoResultado,
        String mensagem,
        boolean podeAvancar) {
    public EstadoVisaoClube {
        elenco = List.copyOf(elenco);
        classificacao = List.copyOf(classificacao);
    }

    public enum Status { CARREGANDO, PRONTO, VAZIO, ERRO }
}
