# features/Setup_Wizard/setup_wizard_repo.py

from sqlalchemy.orm import Session
from shared.orm_models.users_models import UsersModel, TranslationOfficeDataModel, SecurityQuestionModel
from shared.orm_models.license_models import LicenseModel
from features.Setup_Wizard.setup_wizard_models import TranslationOfficeDTO, AdminUserDTO
import bcrypt


class SetupWizardRepository:
    """
    Stateless repository for setup wizard data operations.
    Requires a session to be passed into each method.
    """

    # === Existence Checks === (no changes here)
    def is_license_present(self, session: Session) -> bool:
        return session.query(LicenseModel).first() is not None

    def is_office_present(self, session: Session) -> bool:
        return session.query(TranslationOfficeDataModel).first() is not None

    def is_admin_present(self, session: Session) -> bool:
        return session.query(UsersModel).filter(UsersModel.role == 'admin').first() is not None

    # === Data Persistence === (save_license and save_translation_office are unchanged)
    def save_license(self, session: Session, license_details: dict) -> None:
        license_key = license_details.get("license_key")
        if not license_key:
            raise ValueError("License details dictionary must contain a 'license_key'")

        existing_license = session.query(LicenseModel).filter_by(license_key=license_key).first()

        if existing_license:
            for key, value in license_details.items():
                setattr(existing_license, key, value)
        else:
            new_license = LicenseModel(**license_details)
            session.add(new_license)

        session.commit()

    def save_translation_office(self, session: Session, office_dto: TranslationOfficeDTO, license_key: str) -> None:
        existing_office = session.query(TranslationOfficeDataModel).filter_by(license_key=license_key).first()
        office_data = office_dto.__dict__

        if existing_office:
            for key, value in office_data.items():
                setattr(existing_office, key, value)
        else:
            office_data['license_key'] = license_key
            new_office = TranslationOfficeDataModel(**office_data)
            session.add(new_office)
        session.commit()

    # CHANGE: Renamed method and simplified its signature and logic.
    def save_admin_user(
            self,
            users_session: Session,
            user_dto: AdminUserDTO
    ) -> None:
        """
        Creates the admin user and their security questions in the users DB.
        This no longer interacts with the payroll database.
        """
        try:
            # STEP 1: Create user with bcrypt-hashed password
            password_hash = bcrypt.hashpw(user_dto.password.encode('utf-8'), bcrypt.gensalt())

            new_user = UsersModel(
                username=user_dto.username,
                password_hash=password_hash,
                role='admin',
                display_name=user_dto.display_name,
                avatar_path=None
            )
            users_session.add(new_user)
            users_session.flush()  # Get user.id for the security questions

            # STEP 2: Add security questions with bcrypt-hashed answers
            answer1_hash = bcrypt.hashpw(user_dto.security_answer_1.encode('utf-8'), bcrypt.gensalt())
            question1 = SecurityQuestionModel(
                user_id=new_user.id,
                question=user_dto.security_question_1,
                answer_hash=answer1_hash
            )

            answer2_hash = bcrypt.hashpw(user_dto.security_answer_2.encode('utf-8'), bcrypt.gensalt())
            question2 = SecurityQuestionModel(
                user_id=new_user.id,
                question=user_dto.security_question_2,
                answer_hash=answer2_hash
            )

            users_session.add(question1)
            users_session.add(question2)

            # STEP 3: Commit the transaction
            users_session.commit()

        except Exception:
            users_session.rollback()
            raise
