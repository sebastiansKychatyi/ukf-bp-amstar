<template>
  <v-container class="fill-height" fluid>
    <v-row align="center" justify="center">
      <v-col cols="12" sm="8" md="5" lg="4">
        <!-- Header -->
        <div class="text-center mb-6">
          <v-icon size="64" color="primary" class="mb-4">mdi-lock-check</v-icon>
          <h1 class="text-h4 font-weight-bold">Set New Password</h1>
          <p class="text-body-2 text-medium-emphasis mt-2">
            Enter your reset token and choose a new password
          </p>
        </div>

        <v-card elevation="8" rounded="lg" class="pa-6">
          <v-card-text>
            <!-- Success state -->
            <div v-if="success" class="text-center py-4">
              <v-icon size="64" color="success" class="mb-4">mdi-check-circle</v-icon>
              <p class="text-body-1 mb-2">Password reset successfully!</p>
              <p class="text-body-2 text-medium-emphasis">You can now log in with your new password.</p>
              <v-btn color="primary" class="mt-4" to="/auth/login" prepend-icon="mdi-login">
                Log In
              </v-btn>
            </div>

            <!-- Reset form -->
            <v-form v-else ref="formRef" v-model="valid" @submit.prevent="handleReset">
              <v-alert
                v-if="error"
                type="error"
                variant="tonal"
                closable
                class="mb-4"
                @click:close="error = ''"
              >
                {{ error }}
              </v-alert>

              <v-text-field
                v-model="token"
                label="Reset Token"
                variant="outlined"
                prepend-inner-icon="mdi-key"
                :rules="[(v: string) => !!v || 'Token is required']"
                autocomplete="off"
                class="mb-4"
              />

              <v-text-field
                v-model="newPassword"
                label="New Password"
                :type="showPassword ? 'text' : 'password'"
                variant="outlined"
                prepend-inner-icon="mdi-lock"
                :append-inner-icon="showPassword ? 'mdi-eye' : 'mdi-eye-off'"
                @click:append-inner="showPassword = !showPassword"
                :rules="passwordRules"
                autocomplete="new-password"
                class="mb-6"
              />

              <v-btn
                type="submit"
                color="primary"
                size="large"
                block
                :loading="loading"
                :disabled="!valid"
              >
                Reset Password
              </v-btn>
            </v-form>
          </v-card-text>

          <v-divider class="my-2" />

          <v-card-actions class="justify-center">
            <v-btn variant="text" to="/auth/login" prepend-icon="mdi-arrow-left">
              Back to Login
            </v-btn>
            <v-btn variant="text" to="/auth/forgot-password" prepend-icon="mdi-email">
              Request New Token
            </v-btn>
          </v-card-actions>
        </v-card>
      </v-col>
    </v-row>
  </v-container>
</template>

<script setup lang="ts">
import { ref } from 'vue'

definePageMeta({ middleware: ['guest'] })

const config = useRuntimeConfig()
const apiBase = config.public.apiBaseUrl || 'http://localhost:8000/api/v1'

const formRef = ref()
const valid = ref(false)
const loading = ref(false)
const success = ref(false)
const token = ref('')
const newPassword = ref('')
const showPassword = ref(false)
const error = ref('')

const passwordRules = [
  (v: string) => !!v || 'Password is required',
  (v: string) => v.length >= 8 || 'Password must be at least 8 characters',
]

const handleReset = async () => {
  const { valid: isValid } = await formRef.value.validate()
  if (!isValid) return

  loading.value = true
  error.value = ''

  try {
    await $fetch(`${apiBase}/auth/reset-password`, {
      method: 'POST',
      body: {
        token: token.value,
        new_password: newPassword.value,
      },
    })
    success.value = true
  } catch (err: any) {
    error.value = err.data?.detail || 'Failed to reset password. The token may be invalid or expired.'
  } finally {
    loading.value = false
  }
}
</script>
