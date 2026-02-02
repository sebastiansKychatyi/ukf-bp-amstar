<template>
  <v-container class="fill-height" fluid>
    <v-row align="center" justify="center">
      <v-col cols="12" sm="8" md="5" lg="4">
        <!-- Logo/Header -->
        <div class="text-center mb-6">
          <v-icon size="64" color="primary" class="mb-4">mdi-soccer</v-icon>
          <h1 class="text-h4 font-weight-bold">Welcome Back</h1>
          <p class="text-body-2 text-medium-emphasis mt-2">
            Sign in to your AmStar account
          </p>
        </div>

        <v-card elevation="8" rounded="lg" class="pa-6">
          <v-card-text>
            <v-form ref="formRef" v-model="valid" @submit.prevent="handleLogin">
              <!-- Error Alert -->
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

              <!-- Email Field -->
              <v-text-field
                v-model="formData.username"
                label="Email"
                type="email"
                prepend-inner-icon="mdi-email-outline"
                variant="outlined"
                :rules="emailRules"
                required
                autocomplete="email"
                class="mb-2"
              />

              <!-- Password Field -->
              <v-text-field
                v-model="formData.password"
                :type="showPassword ? 'text' : 'password'"
                label="Password"
                prepend-inner-icon="mdi-lock-outline"
                :append-inner-icon="showPassword ? 'mdi-eye-off' : 'mdi-eye'"
                variant="outlined"
                :rules="passwordRules"
                required
                autocomplete="current-password"
                class="mb-2"
                @click:append-inner="showPassword = !showPassword"
              />

              <!-- Remember Me & Forgot Password -->
              <div class="d-flex justify-space-between align-center mb-4">
                <v-checkbox
                  v-model="rememberMe"
                  label="Remember me"
                  density="compact"
                  hide-details
                  color="primary"
                />
                <a href="#" class="text-primary text-decoration-none text-body-2">
                  Forgot password?
                </a>
              </div>

              <!-- Submit Button -->
              <v-btn
                type="submit"
                color="primary"
                size="large"
                block
                :loading="loading"
                :disabled="!valid"
              >
                <v-icon start>mdi-login</v-icon>
                Sign In
              </v-btn>
            </v-form>
          </v-card-text>

          <v-divider class="my-4" />

          <!-- Register Link -->
          <v-card-text class="text-center pa-0">
            <span class="text-medium-emphasis">Don't have an account?</span>
            <NuxtLink to="/auth/register" class="text-primary text-decoration-none font-weight-medium ml-1">
              Create Account
            </NuxtLink>
          </v-card-text>
        </v-card>

        <!-- Back to Home -->
        <div class="text-center mt-6">
          <NuxtLink to="/" class="text-medium-emphasis text-decoration-none">
            <v-icon size="small" class="mr-1">mdi-arrow-left</v-icon>
            Back to Home
          </NuxtLink>
        </div>
      </v-col>
    </v-row>
  </v-container>
</template>

<script setup lang="ts">
const { login } = useAuth()
const router = useRouter()

const formRef = ref()
const valid = ref(false)
const showPassword = ref(false)

const formData = ref({
  username: '',
  password: '',
})

const rememberMe = ref(false)
const loading = ref(false)
const error = ref('')

const emailRules = [
  (v: string) => !!v || 'Email is required',
  (v: string) => /.+@.+\..+/.test(v) || 'Please enter a valid email',
]

const passwordRules = [
  (v: string) => !!v || 'Password is required',
  (v: string) => v.length >= 6 || 'Minimum 6 characters',
]

const handleLogin = async () => {
  const { valid: isValid } = await formRef.value.validate()
  if (!isValid) return

  loading.value = true
  error.value = ''

  const result = await login(formData.value)

  loading.value = false

  if (result.success) {
    const redirect = router.currentRoute.value.query.redirect as string
    router.push(redirect || '/profile')
  } else {
    error.value = result.error || 'Invalid email or password'
  }
}
</script>

<style scoped>
.v-container {
  background: linear-gradient(135deg, #1a237e 0%, #3949ab 100%);
  min-height: 100vh;
}
</style>
