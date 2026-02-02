<template>
  <v-container class="fill-height" fluid>
    <v-row align="center" justify="center">
      <v-col cols="12" sm="10" md="7" lg="5">
        <!-- Logo/Header -->
        <div class="text-center mb-6">
          <v-icon size="64" color="primary" class="mb-4">mdi-soccer</v-icon>
          <h1 class="text-h4 font-weight-bold">Create Account</h1>
          <p class="text-body-2 text-medium-emphasis mt-2">
            Join AmStar Football Platform
          </p>
        </div>

        <v-card elevation="8" rounded="lg" class="pa-6">
          <v-card-text>
            <v-form ref="formRef" v-model="valid" @submit.prevent="handleRegister">
              <!-- Success Alert -->
              <v-alert
                v-if="success"
                type="success"
                variant="tonal"
                class="mb-4"
              >
                <v-alert-title>Registration successful!</v-alert-title>
                Redirecting to login...
              </v-alert>

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

              <v-row>
                <!-- Full Name -->
                <v-col cols="12" md="6">
                  <v-text-field
                    v-model="formData.full_name"
                    label="Full Name"
                    prepend-inner-icon="mdi-account-outline"
                    variant="outlined"
                    density="comfortable"
                  />
                </v-col>

                <!-- Username -->
                <v-col cols="12" md="6">
                  <v-text-field
                    v-model="formData.username"
                    label="Username"
                    prepend-inner-icon="mdi-at"
                    variant="outlined"
                    density="comfortable"
                    :rules="usernameRules"
                    required
                  />
                </v-col>

                <!-- Email -->
                <v-col cols="12">
                  <v-text-field
                    v-model="formData.email"
                    label="Email"
                    type="email"
                    prepend-inner-icon="mdi-email-outline"
                    variant="outlined"
                    density="comfortable"
                    :rules="emailRules"
                    required
                  />
                </v-col>

                <!-- Role Selection -->
                <v-col cols="12">
                  <p class="text-subtitle-2 font-weight-medium mb-3">Select Your Role</p>
                  <v-item-group v-model="formData.role" mandatory>
                    <v-row>
                      <v-col v-for="role in roles" :key="role.value" cols="12" md="4">
                        <v-item v-slot="{ isSelected, toggle }" :value="role.value">
                          <v-card
                            :color="isSelected ? 'primary' : undefined"
                            :variant="isSelected ? 'elevated' : 'outlined'"
                            class="pa-4 cursor-pointer role-card"
                            height="100%"
                            @click="toggle"
                          >
                            <div class="text-center">
                              <v-icon :color="isSelected ? 'white' : 'primary'" size="36" class="mb-2">
                                {{ role.icon }}
                              </v-icon>
                              <div :class="isSelected ? 'text-white' : 'text-high-emphasis'" class="font-weight-bold">
                                {{ role.title }}
                              </div>
                              <div :class="isSelected ? 'text-white' : 'text-medium-emphasis'" class="text-caption mt-1">
                                {{ role.description }}
                              </div>
                            </div>
                          </v-card>
                        </v-item>
                      </v-col>
                    </v-row>
                  </v-item-group>
                </v-col>

                <!-- Password -->
                <v-col cols="12" md="6">
                  <v-text-field
                    v-model="formData.password"
                    :type="showPassword ? 'text' : 'password'"
                    label="Password"
                    prepend-inner-icon="mdi-lock-outline"
                    :append-inner-icon="showPassword ? 'mdi-eye-off' : 'mdi-eye'"
                    variant="outlined"
                    density="comfortable"
                    :rules="passwordRules"
                    required
                    hint="Minimum 6 characters"
                    @click:append-inner="showPassword = !showPassword"
                  />
                </v-col>

                <!-- Confirm Password -->
                <v-col cols="12" md="6">
                  <v-text-field
                    v-model="confirmPassword"
                    :type="showConfirmPassword ? 'text' : 'password'"
                    label="Confirm Password"
                    prepend-inner-icon="mdi-lock-check-outline"
                    :append-inner-icon="showConfirmPassword ? 'mdi-eye-off' : 'mdi-eye'"
                    variant="outlined"
                    density="comfortable"
                    :rules="confirmPasswordRules"
                    required
                    @click:append-inner="showConfirmPassword = !showConfirmPassword"
                  />
                </v-col>

                <!-- Submit Button -->
                <v-col cols="12">
                  <v-btn
                    type="submit"
                    color="primary"
                    size="large"
                    block
                    :loading="loading"
                    :disabled="!valid || success"
                  >
                    <v-icon start>mdi-account-plus</v-icon>
                    Create Account
                  </v-btn>
                </v-col>
              </v-row>
            </v-form>
          </v-card-text>

          <v-divider class="my-4" />

          <!-- Login Link -->
          <v-card-text class="text-center pa-0">
            <span class="text-medium-emphasis">Already have an account?</span>
            <NuxtLink to="/auth/login" class="text-primary text-decoration-none font-weight-medium ml-1">
              Sign In
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
import { UserRole } from '@/types/auth'

const { register } = useAuth()
const router = useRouter()

const formRef = ref()
const valid = ref(false)
const showPassword = ref(false)
const showConfirmPassword = ref(false)

const formData = ref({
  email: '',
  username: '',
  full_name: '',
  password: '',
  role: UserRole.PLAYER,
})

const confirmPassword = ref('')
const loading = ref(false)
const error = ref('')
const success = ref(false)

const roles = [
  {
    value: UserRole.PLAYER,
    title: 'Player',
    description: 'Join matches and teams',
    icon: 'mdi-run',
  },
  {
    value: UserRole.CAPTAIN,
    title: 'Captain',
    description: 'Manage your team',
    icon: 'mdi-crown',
  },
  {
    value: UserRole.REFEREE,
    title: 'Referee',
    description: 'Officiate matches',
    icon: 'mdi-whistle',
  },
]

const emailRules = [
  (v: string) => !!v || 'Email is required',
  (v: string) => /.+@.+\..+/.test(v) || 'Please enter a valid email',
]

const usernameRules = [
  (v: string) => !!v || 'Username is required',
  (v: string) => v.length >= 3 || 'Minimum 3 characters',
]

const passwordRules = [
  (v: string) => !!v || 'Password is required',
  (v: string) => v.length >= 6 || 'Minimum 6 characters',
]

const confirmPasswordRules = [
  (v: string) => !!v || 'Please confirm your password',
  (v: string) => v === formData.value.password || 'Passwords do not match',
]

const handleRegister = async () => {
  const { valid: isValid } = await formRef.value.validate()
  if (!isValid) return

  loading.value = true
  error.value = ''
  success.value = false

  const result = await register(formData.value)

  loading.value = false

  if (result.success) {
    success.value = true
    setTimeout(() => {
      router.push('/auth/login')
    }, 2000)
  } else {
    error.value = result.error || 'Registration failed. Please try again.'
  }
}
</script>

<style scoped>
.v-container {
  background: linear-gradient(135deg, #1a237e 0%, #3949ab 100%);
  min-height: 100vh;
}

.role-card {
  transition: all 0.2s ease;
}

.role-card:hover {
  transform: translateY(-2px);
}

.cursor-pointer {
  cursor: pointer;
}
</style>
