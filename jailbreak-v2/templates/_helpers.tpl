{{/*
Expand the name of the chart.
*/}}
{{- define "jailbreak-distilbert.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified app name.
*/}}
{{- define "jailbreak-distilbert.fullname" -}}
{{- if .Values.fullnameOverride }}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- $name := default .Chart.Name .Values.nameOverride }}
{{- if contains $name .Release.Name }}
{{- .Release.Name | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" }}
{{- end }}
{{- end }}
{{- end }}

{{/*
Create chart name and version as used by the chart label.
*/}}
{{- define "jailbreak-distilbert.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Common labels
*/}}
{{- define "jailbreak-distilbert.labels" -}}
helm.sh/chart: {{ include "jailbreak-distilbert.chart" . }}
{{ include "jailbreak-distilbert.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
app.kubernetes.io/component: service
service-type: content-moderation
model-version: {{ .Values.model.version }}
training-accuracy: {{ .Values.model.accuracy }}
training-f1-score: {{ .Values.model.f1Score }}
{{- end }}

{{/*
Selector labels
*/}}
{{- define "jailbreak-distilbert.selectorLabels" -}}
app.kubernetes.io/name: {{ include "jailbreak-distilbert.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{/*
Create the name of the service account to use
*/}}
{{- define "jailbreak-distilbert.serviceAccountName" -}}
{{- if .Values.serviceAccount.create }}
{{- default (include "jailbreak-distilbert.fullname" .) .Values.serviceAccount.name }}
{{- else }}
{{- default "default" .Values.serviceAccount.name }}
{{- end }}
{{- end }}

{{/*
Create the image name
*/}}
{{- define "jailbreak-distilbert.image" -}}
{{- $registry := .Values.image.registry -}}
{{- $repository := .Values.image.repository -}}
{{- $tag := .Values.image.tag | default .Chart.AppVersion -}}
{{- if $registry }}
{{- printf "%s/%s:%s" $registry $repository $tag -}}
{{- else }}
{{- printf "%s:%s" $repository $tag -}}
{{- end }}
{{- end }}