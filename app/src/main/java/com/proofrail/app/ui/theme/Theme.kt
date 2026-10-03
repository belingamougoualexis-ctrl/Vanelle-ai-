package com.proofrail.app.ui.theme

import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.lightColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.TextStyle
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.sp

private val Navy = Color(0xFF0B1220)
private val Blue = Color(0xFF2878FF)
private val Surface = Color(0xFFF6F8FC)

private val Colors = lightColorScheme(
    primary = Blue,
    onPrimary = Color.White,
    primaryContainer = Color(0xFFDCE9FF),
    onPrimaryContainer = Navy,
    secondary = Color(0xFF4F6280),
    background = Surface,
    onBackground = Navy,
    surface = Color.White,
    onSurface = Navy,
    error = Color(0xFFBA1A1A)
)

@Composable
fun ProofRailTheme(content: @Composable () -> Unit) {
    MaterialTheme(
        colorScheme = Colors,
        typography = androidx.compose.material3.Typography(
            bodyLarge = TextStyle(fontSize = 16.sp, lineHeight = 24.sp),
            titleLarge = TextStyle(fontSize = 20.sp, fontWeight = FontWeight.Bold),
            headlineSmall = TextStyle(fontSize = 26.sp, fontWeight = FontWeight.ExtraBold)
        ),
        content = content
    )
}
