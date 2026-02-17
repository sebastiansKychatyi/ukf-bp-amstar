<template>
  <v-container class="fill-height" fluid>
    <v-row align="center" justify="center">
      <v-col cols="12" sm="8" md="5" lg="4">
        <!-- Header -->
        <div class="text-center mb-6">
          <v-icon size="64" color="primary" class="mb-4">mdi-lock-reset</v-icon>
          <h1 class="text-h4 font-weight-bold">Reset Password</h1>
          <p class="text-body-2 text-medium-emphasis mt-2">
            Enter your email address to receive a reset token
          </p>
        </div>

        <v-card elevation="8" rounded="lg" class="pa-6">
          <v-card-text>
            <!-- Success state -->
            <div v-if="submitted" class="text-center py-4">
              <v-icon size="64" color="success" class="mb-4">mdi-check-circle</v-icon>
              <p class="text-body-1 mb-2">{{ successMessage }}</p>
              <p class="text-body-2 text-medium-emphasis">
                Check the server console for your reset token (development mode).
              </p>
              <v-btn
                color="primary"
                class="mt-4"
                to="/auth/reset-password"
                prepend-icon="mdi-key"
              >
                Enter Reset Token
              </v-btn>
            </div>

            <!-- Request form -->
            <v-form v-else ref="formRef" v-model="valid" @submit.prevent="handleSubmit">
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
                v-model="email"
                label="Email address"
                type="email"
                variant="outlined"
                prepend-inner-icon="mdi-email"
                :rules="emailRules"
                autocomplete="email"
                class="mb-4"
              />

              <v-btn
                type="submit"
                color="primary"
                size="large"
                block
                :loading="loading"
                :disabled="!valid"
              >
                Send Reset Token
              </v-btn>
            </v-form>
          </v-card-text>

          <v-divider class="my-2" />

          <v-card-actions class="justify-center">
            <v-btn variant="text" to="/auth/login" prepend-icon="mdi-arrow-left">
              Back to Login
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
const submitted = ref(false)
const email = ref('')
const error = ref('')
const successMessage = ref('')

const emailRules = [
  (v: string) => !!v || 'Email is required',
  (v: string) => /.+@.+\..+/.test(v) || 'Enter a valid email address',
]

const handleSubmit = async () => {
  const { valid: isValid } = await formRef.value.validate()
  if (!isValid) return

  loading.value = true
  error.value = ''

  try {
    const data = await $fetch<{ message: string }>(`${apiBase}/auth/forgot-password`, {
      method: 'POST',
      body: { email: email.value },
    })
    successMessage.value = data.message
    submitted.value = true
  } catch (err: any) {
    error.value = err.data?.detail || 'Something went wrong. Please try again.'
  } finally {
    loading.value = false
  }
}
</script>
