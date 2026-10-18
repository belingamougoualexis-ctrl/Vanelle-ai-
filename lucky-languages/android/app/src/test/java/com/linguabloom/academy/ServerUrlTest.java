package com.linguabloom.academy;

import org.junit.Test;
import static org.junit.Assert.*;

public class ServerUrlTest {
    @Test public void addsHttpAndRemovesTrailingSlash() {
        assertEquals("http://192.168.1.20:8000", ServerUrl.normalize("192.168.1.20:8000/"));
    }
    @Test public void preservesHttpsPath() {
        assertEquals("https://academy.example/api", ServerUrl.normalize("https://academy.example/api/"));
    }
    @Test(expected = IllegalArgumentException.class) public void rejectsEmptyAddress() {
        ServerUrl.normalize("  ");
    }
    @Test(expected = IllegalArgumentException.class) public void rejectsUnsupportedScheme() {
        ServerUrl.normalize("ftp://academy.example");
    }
}
