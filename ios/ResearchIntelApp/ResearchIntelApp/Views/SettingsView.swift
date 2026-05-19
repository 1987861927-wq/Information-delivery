import SwiftUI

struct SettingsView: View {
    @State private var notificationsEnabled = false
    @State private var pushTime = Date()

    var body: some View {
        NavigationStack {
            Form {
                Section("推送") {
                    Toggle("每日简报推送", isOn: $notificationsEnabled)
                    DatePicker("推送时间", selection: $pushTime, displayedComponents: .hourAndMinute)
                    Button("请求通知权限") {
                        Task {
                            notificationsEnabled = (try? await NotificationManager.shared.requestAuthorization()) ?? false
                        }
                    }
                }

                Section("摘要偏好") {
                    Text("默认生成中文结构化摘要，后续支持摘要长度和关注维度设置。")
                        .foregroundStyle(.secondary)
                }
            }
            .navigationTitle("我的")
        }
    }
}
