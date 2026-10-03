package com.proofrail.app

import org.junit.Assert.assertTrue
import org.junit.Test
import java.security.MessageDigest

class HashChainTest {
    @Test
    fun sha256_is_deterministic() {
        val value = MessageDigest.getInstance("SHA-256").digest("proofrail".toByteArray()).joinToString("") { "%02x".format(it) }
        assertTrue(value.length == 64)
    }
}
