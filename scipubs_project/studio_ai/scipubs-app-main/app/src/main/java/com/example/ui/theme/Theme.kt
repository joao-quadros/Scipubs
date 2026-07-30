package com.example.ui.theme

import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.darkColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.ui.graphics.Color

private val SciPubsDarkColorScheme = darkColorScheme(
    primary = CoralRedAccent,
    onPrimary = Color.White,
    secondary = TealAccent,
    onSecondary = Color.White,
    background = DeepNavyBackground,
    onBackground = LightText,
    surface = DarkCardContainer,
    onSurface = LightText,
    surfaceVariant = DarkCardContainerElevated,
    onSurfaceVariant = MutedText,
    outline = MutedText
)

@Composable
fun SciPubsTheme(
    content: @Composable () -> Unit
) {
    MaterialTheme(
        colorScheme = SciPubsDarkColorScheme,
        typography = Typography,
        content = content
    )
}
