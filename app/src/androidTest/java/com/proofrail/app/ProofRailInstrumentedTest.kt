package com.proofrail.app

import android.content.Context
import androidx.test.core.app.ApplicationProvider
import com.proofrail.app.data.ProofDatabase
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Before
import org.junit.Test

class ProofRailInstrumentedTest {
    private lateinit var db: ProofDatabase

    @Before
    fun resetWorkspace() {
        val context = ApplicationProvider.getApplicationContext<Context>()
        context.deleteDatabase("proofrail.db")
        db = ProofDatabase(context)
    }

    @Test
    fun coreWorkflow_persists_and_verifies_real_state() {
        val controlId = db.createControl(
            name = "Privileged access",
            requirement = "Privileged access must have current approval evidence",
            threshold = 1
        )
        assertEquals(1, db.dashboard().controls)
        assertEquals("INSUFFICIENT_EVIDENCE", db.runCheck(controlId))

        db.addEvidence(
            controlId = controlId,
            source = "manual observation",
            statement = "Approval record inspected on device",
            observedAt = "2026-10-03T08:00:00Z"
        )
        assertEquals("PASS", db.runCheck(controlId))

        val decisionId = db.createDecision(
            title = "Enable sensitive automated action",
            details = "An explicit human authorization is required before proceeding",
            risk = "HIGH"
        )
        assertEquals(1, db.dashboard().decisionsPending)
        assertEquals("APPROVED", db.decide(decisionId, approve = true, actor = "Test operator"))
        assertEquals(0, db.dashboard().decisionsPending)

        val before = db.dashboard()
        assertTrue(before.auditValid)
        assertTrue(before.auditEntries >= 5)

        val backup = db.exportJson()
        assertTrue(backup.contains("proofrail-workspace"))

        db.importJson(backup)

        val after = db.dashboard()
        assertEquals(before.controls, after.controls)
        assertEquals(before.evidence, after.evidence)
        assertEquals(before.checks, after.checks)
        assertEquals(before.auditEntries, after.auditEntries)
        assertTrue(after.auditValid)
        assertFalse(db.listEvidence().isEmpty())
        assertFalse(db.listAudit().isEmpty())
    }
}
