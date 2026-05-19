import Foundation
import UserNotifications

final class NotificationManager {
    static let shared = NotificationManager()

    private init() {}

    func requestAuthorization() async throws -> Bool {
        try await UNUserNotificationCenter.current().requestAuthorization(options: [.alert, .badge, .sound])
    }
}
