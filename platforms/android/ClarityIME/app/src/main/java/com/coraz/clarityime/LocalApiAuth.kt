package com.coraz.clarityime

import android.content.Context
import java.io.File

/** Reads loopback API token for mutating core endpoints (v0.4+). */
object LocalApiAuth {
    private const val ENV_TOKEN = "CLARITYIME_API_TOKEN"
    private const val ENV_ROOT = "CLARITYIME_ROOT"

    fun token(context: Context? = null): String? {
        System.getenv(ENV_TOKEN)?.trim()?.takeIf { it.isNotEmpty() }?.let { return it }
        context?.let {
            ClarityPrefs.prefs(it).getString(ClarityPrefs.KEY_LOCAL_API_TOKEN, null)
                ?.trim()
                ?.takeIf { t -> t.isNotEmpty() }
                ?.let { t -> return t }
        }
        tokenFileCandidates().firstNotNullOfOrNull { path ->
            runCatching {
                val f = File(path)
                if (f.isFile) f.readText().trim().takeIf { it.isNotEmpty() } else null
            }.getOrNull()
        }?.let { return it }
        return null
    }

    private fun tokenFileCandidates(): List<String> {
        val root = System.getenv(ENV_ROOT)?.trim()?.takeIf { it.isNotEmpty() }
        val paths = mutableListOf<String>()
        if (!root.isNullOrEmpty()) {
            paths.add("$root/data/.local_api_token")
        }
        // Termux sidecar default when user clones repo to ~/clarityime
        paths.add("/data/data/com.termux/files/home/clarityime/data/.local_api_token")
        return paths
    }
}
