package com.coraz.clarityime

import android.content.Context
import android.content.SharedPreferences

/** SharedPreferences keys for ClarityIME. */
object ClarityPrefs {
    const val NAME = "clarityime"
    const val KEY_ONBOARDING_DONE = "onboarding_completed"
    const val KEY_AUDIENCE_MODE = "audience_mode"
    const val KEY_DEFAULT_CONTACT = "default_contact"
    const val KEY_ASR_LANGUAGE = "asr_language"
    const val KEY_AUTO_APPLY_TOP = "auto_apply_top"
    const val KEY_CLOUD_SYNC = "cloud_sync"
    const val KEY_AGGREGATE_RESEARCH = "aggregate_research"
    const val KEY_LOCAL_API_TOKEN = "local_api_token"

    fun prefs(context: Context): SharedPreferences =
        context.getSharedPreferences(NAME, Context.MODE_PRIVATE)

    fun isOnboardingDone(context: Context): Boolean =
        prefs(context).getBoolean(KEY_ONBOARDING_DONE, false)

    fun setOnboardingDone(context: Context, done: Boolean = true) {
        prefs(context).edit().putBoolean(KEY_ONBOARDING_DONE, done).apply()
    }
}
