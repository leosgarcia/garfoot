package br.com.garfoot.core.service;

import br.com.garfoot.core.model.jogador.DadosRatingJogador;
import br.com.garfoot.core.model.jogador.Posicao;
import br.com.garfoot.core.model.jogador.RatingJogador;
import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertTrue;

class GeradorRatingJogadorTest {
    private final GeradorRatingJogador gerador = new GeradorRatingJogador();

    @Test
    void generatesRatingsInsideTheGameScale() {
        RatingJogador rating = gerador.gerar(new DadosRatingJogador(
                22, 180, 25_000_000, 80, 6_000, 30, 15, 10, Posicao.ATA));

        assertTrue(rating.tecnica() >= 20 && rating.tecnica() <= 100);
        assertTrue(rating.potencial() >= 20 && rating.potencial() <= 100);
    }

    @Test
    void youngPlayerHasMorePotentialThanEquivalentVeteran() {
        DadosRatingJogador jovem = new DadosRatingJogador(20, 180, 10_000_000, 50, 4_000, 10, 8, 2, Posicao.MEI);
        DadosRatingJogador veterano = new DadosRatingJogador(34, 180, 10_000_000, 50, 4_000, 10, 8, 2, Posicao.MEI);

        assertTrue(gerador.gerar(jovem).potencial() > gerador.gerar(veterano).potencial());
    }

    @Test
    void positionChangesSpecializedRatings() {
        DadosRatingJogador atacante = new DadosRatingJogador(25, 180, 5_000_000, 40, 3_000, 20, 5, 2, Posicao.ATA);
        DadosRatingJogador zagueiro = new DadosRatingJogador(25, 190, 5_000_000, 40, 3_000, 2, 1, 2, Posicao.ZAG);

        assertTrue(gerador.gerar(atacante).finalizacao() > gerador.gerar(zagueiro).finalizacao());
        assertTrue(gerador.gerar(zagueiro).marcacao() > gerador.gerar(atacante).marcacao());
    }

    @Test
    void sameInputProducesSameRating() {
        DadosRatingJogador dados = new DadosRatingJogador(27, 178, 2_000_000, 30, 2_000, 5, 7, 1, Posicao.VOL);

        assertEquals(gerador.gerar(dados), gerador.gerar(dados));
    }
}
