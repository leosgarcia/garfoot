package br.com.garfoot.persistence;

import jakarta.persistence.EntityManagerFactory;
import jakarta.persistence.Persistence;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.HashMap;
import java.util.Map;

public final class FabricaPersistencia {
    private FabricaPersistencia() { }

    public static EntityManagerFactory criar() {
        String urlConfigurada = System.getProperty("garfoot.db.url");
        if (urlConfigurada == null || urlConfigurada.isBlank()) {
            urlConfigurada = System.getenv("GARFOOT_DB_URL");
        }
        if (urlConfigurada != null && !urlConfigurada.isBlank()) {
            return criar(urlConfigurada, valor("garfoot.db.user", "GARFOOT_DB_USER", "sa"),
                    valor("garfoot.db.password", "GARFOOT_DB_PASSWORD", ""));
        }
        Path diretorio = Path.of(System.getProperty("user.home"), ".garfoot").toAbsolutePath();
        try {
            Files.createDirectories(diretorio);
        } catch (IOException exception) {
            throw new IllegalStateException("could not create local Garfoot data directory", exception);
        }
        String url = "jdbc:h2:file:" + diretorio.resolve("garfoot").toString() + ";DB_CLOSE_ON_EXIT=FALSE";
        return criar(url, "sa", "");
    }

    public static EntityManagerFactory criar(String jdbcUrl, String usuario, String senha) {
        if (jdbcUrl == null || jdbcUrl.isBlank()) throw new IllegalArgumentException("jdbcUrl must not be blank");
        String driver;
        if (jdbcUrl.startsWith("jdbc:postgresql:")) driver = "org.postgresql.Driver";
        else if (jdbcUrl.startsWith("jdbc:h2:")) driver = "org.h2.Driver";
        else throw new IllegalArgumentException("only H2 and PostgreSQL JDBC URLs are supported");
        Map<String, Object> propriedades = new HashMap<>();
        propriedades.put("jakarta.persistence.jdbc.driver", driver);
        propriedades.put("jakarta.persistence.jdbc.url", jdbcUrl);
        propriedades.put("jakarta.persistence.jdbc.user", usuario == null ? "" : usuario);
        propriedades.put("jakarta.persistence.jdbc.password", senha == null ? "" : senha);
        propriedades.put("hibernate.hbm2ddl.auto", "update");
        propriedades.put("hibernate.show_sql", "false");
        return Persistence.createEntityManagerFactory("garfoot-local", propriedades);
    }

    private static String valor(String propriedade, String variavel, String padrao) {
        String valor = System.getProperty(propriedade);
        if (valor == null || valor.isBlank()) valor = System.getenv(variavel);
        return valor == null || valor.isBlank() ? padrao : valor;
    }
}
